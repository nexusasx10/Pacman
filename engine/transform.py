from engine.components import Component
from engine.geometry import Matrix3x3


class Transform2d(Component):

    def __init__(self, owner):
        super().__init__(owner)

        self._matrix = Matrix3x3.identity()

        self.parent = None
        self._children = []

    def translate(self, x, y):
        pass

    def rotate(self, angle):
        pass
