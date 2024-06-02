from typing import Optional


class DataClass:  # TODO: This is deprecated
    def __eq__(self, other):
        if other is None or not isinstance(other, type(self)):
            return False
        for field in self.__dict__.keys():
            if self.__dict__[field] != other.__dict__[field]:
                return False
        return True

    def __hash__(self):
        iterable = map(hash, self.__dict__.values())
        result = next(iterable)
        for item in iterable:
            result ^= item
        return result


class classproperty:

    def __init__(self, getter):
        self._getter = getter

    def __get__(self, owner, cls):
        return self._getter(cls)


def value_or_default(value, default):
    if value is not None:
        return value
    return default


def try_call(func, default_result=None, *args, **kwargs):
    if func is not None:
        return func(*args, **kwargs)
    else:
        return default_result
