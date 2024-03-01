from engine.components import ComponentContainer


class Actor(ComponentContainer):

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __repr__(self):
        return f'Actor(name=\'{self.name}\')'
