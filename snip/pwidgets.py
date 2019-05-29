import progressbar


class DynamicProgressString(progressbar.DynamicMessage):
    '''Displays a custom string, preformatted.'''

    def __call__(self, progress, data):
        val = data['dynamic_messages'][self.name]
        if val:
            assert isinstance(val, str)
            return val
        else:
            return "[(" + self.name + ")]"
