import snip.stream
import sys
import traceback


def write(i):
    print("Print, standard", i)
    sys.stdout.write("Write to stdout\n")
    sys.stderr.write("Write to stderr\n")
    assert False


with snip.stream.std_redirected("out_only.txt", tee=True):
    try:
        write(1)
    except:
        traceback.print_exc()
        # raise

write(2)
# with snip.stream.std_redirected("out_2.txt", "err_2.txt"):
#     write()
