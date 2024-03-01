

class Delegate:

    __slots__ = ['callbacks']

    def __init__(self):
        self.callbacks = []

    def __iadd__(self, callback):
        self.callbacks.append(callback)
        return self

    def __isub__(self, callback):
        try:
            self.callbacks.remove(callback)
        except ValueError:
            pass
        self.callbacks.remove(callback)
        return self

    def __call__(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)

    def clear(self):
        self.callbacks.clear()
