

class MultiDelegate:

    __slots__ = '_invocation_list'

    def __init__(self):
        self._invocation_list = []

    def __call__(self, *args, **kwargs):
        for callback in self._invocation_list:
            callback(*args, **kwargs)

    def __iadd__(self, callback):
        self._invocation_list.append(callback)
        return self

    def __isub__(self, callback):
        try:
            self._invocation_list.remove(callback)
        except ValueError:
            pass
        return self

    def clear(self):
        self._invocation_list.clear()


class Event(MultiDelegate):
    pass


def event_handler(func):
    func.handler_for = func.__name__.lstrip('on_') + '_event'
    return func
