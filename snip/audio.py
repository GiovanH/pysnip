import pyaudio
import wave
from contextlib import contextmanager
# import struct

import progressbar

CHUNK = 1024
WIDTH = 2
CHANNELS = 2
RATE = 44100
FORMAT = pyaudio.paInt16


@contextmanager
def wrap_pyaudio():
    p = pyaudio.PyAudio()
    try:
        yield p
    finally:
        p.terminate()


@contextmanager
def wrap_open(p, *args, **kwargs_patch):
    kwargs = dict(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE
    )
    kwargs.update(kwargs_patch)
    print(kwargs)
    stream = p.open(
        *args,
        **kwargs)
    try:
        yield stream
    finally:
        stream.stop_stream()
        stream.close()


def getAudioBar(name=None):
    format_time = dict(
        format_not_started='--:--:--',
        format_finished='%(elapsed)5s / %(elapsed)5s',
        format='%(elapsed)5s / %(eta)5s',
        format_zero='00:00:00',
        format_NA='--:--:--'
    )
    widgets = [
        ("[{n}] ".format(n=name) if name else ''),
        # ' ', progressbar.SimpleProgress(format='%(value_s)s of %(max_value_s)s'),
        ' ', progressbar.Bar(),
        ' ', progressbar.AdaptiveETA(**format_time),
    ]
    return progressbar.ProgressBar(widgets=widgets)


def wrap_stream_frames(stream, rate, chunk, seconds, name=None):
    for i in getAudioBar(name=name)(range(0, int(rate / chunk * seconds))):
    # for i in range(0, int(rate / chunk * seconds)):
    # from statistics import mean
    # from sys import stderr
        frame = stream.read(chunk)
        # if i % 4 == 0:
        #     med = 256
        #     rat = (med + mean(struct.unpack("<{}h".format(int(chunk * 2)), frame))) / (2 * med)
        #     val = str(min(int(rat * 10), 9))
        #     stderr.write(val)
        #     stderr.flush()
        yield frame


def wrap_list_frames(frames, name=None):
    for frame in getAudioBar(name=name)(frames):
        yield frame


class Wavedata():

    def __init__(self, name=None, frames=None, width=2, channels=2, rate=44100, chunk=1024, format=pyaudio.paInt16):
        super(Wavedata, self).__init__()
        if not frames:
            frames = list()
        self.name = name
        self.frames = frames
        self.width = width
        self.channels = channels
        self.rate = rate
        self.chunk = chunk
        self.format = format

    def getLength(self):
        return (self.chunk * len(self.frames)) / self.rate

    def play(self):
        with wrap_pyaudio() as p:
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                output=True
            )
            try:
                for frame in wrap_list_frames(self.frames, name=self.name):
                    stream.write(frame)
            finally:
                stream.stop_stream()
                stream.close()

    def record(self, seconds, label="RECORD"):
        with wrap_pyaudio() as p:
            stream = p.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True
            )
            try:
                self.frames.clear()
                for frame in wrap_stream_frames(stream, self.rate, self.chunk, seconds, name=label):
                    self.frames.append(frame)
            finally:
                stream.stop_stream()
                stream.close()
        return self

    def save(self, outpath):
        with wrap_pyaudio() as p:
            with wave.open(outpath, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(p.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.frames))
        return outpath


# def playfile(path, name=None):
#     with wave.open(path, 'rb') as wf:
#         with wrap_pyaudio() as p:
#             basekwargs = dict(
#                 format=p.get_format_from_width(wf.getsampwidth()),
#                 channels=wf.getnchannels(),
#                 rate=wf.getframerate()
#             )
#             with wrap_open(p, **basekwargs, output=True) as stream:
#                 for frame in wrap_stream_frames(stream, **basekwargs, name=name):
#                     stream.write(frame)


def load(filepath):
    with wrap_pyaudio() as p:
        with wave.open(filepath, 'rb') as wf:
            basekwargs = dict(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate()
            )

            wavefile = Wavedata(**basekwargs, name=filepath)

            frame = wf.readframes(CHUNK)

            while frame:
                wavefile.frames.append(frame)
                frame = wf.readframes(CHUNK)
    return wavefile
