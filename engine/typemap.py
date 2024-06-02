

class TypeMap:

    def __init__(self, factory=None):
        self._objs = {}
        self._factory = factory

    def __setitem__(self, type_, obj):
        if obj is None:
            raise KeyError()  # TODO: Make normal error
        self.add(type_, obj)

    def __getitem__(self, type_):
        obj = self.get(type_)
        if obj is None:
            raise KeyError(type_)  # TODO: Make normal error
        return obj

    def get(self, type_):
        # todo type check
        obj = self._objs.get(type_)
        if obj is not None:
            return obj

        # todo better performance, measure
        for cur_type, cur_obj in self._objs.items():
            if issubclass(cur_type, type_):
                return cur_obj

    def add(self, type_, obj=None):
        # todo а если несколько компонентов с наследующимися типами?
        if obj is None:
            if self._factory:
                obj = type_(self)
            else:
                obj = type_()
        self._objs[type_] = obj
        return obj

    def remove(self, type_):
        raise NotImplementedError()
