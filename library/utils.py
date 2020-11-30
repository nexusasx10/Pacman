

class DataClass:
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


class Services:
    def register(self, name, service):
        self.__dict__[name] = service
