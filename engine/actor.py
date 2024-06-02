from engine.typemap import TypeMap


class Actor(TypeMap):

    _aliases = {}

    def __init__(self, name: str):
        super().__init__(lambda t: t(self))
        self.name = name

    def __repr__(self):
        return f'Actor(name=\'{self.name}\')'

    def __getattr__(self, key):
        type_ = self._aliases.get(key)
        if type_ is not None:
            return self[type_]
        return self.__dict__[key]
