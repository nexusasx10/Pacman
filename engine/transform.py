from math import cos, sin

from engine.components import Component
from library.geometry import Vector
from library.utils import not_none_or_default


class Transform(Component):

    def __init__(self, owner, parent=None, position=None, rotation=None):
        super().__init__(owner)

        self.position = not_none_or_default(position, Vector.zero())
        self.rotation = not_none_or_default(rotation, 0)
        self.parent = parent
        self.children = []

    def move(self, offset):
        self.position += offset
        for child in self.children:
            child.move(offset)

    def rotate(self, angle):
        self.rotation += angle
        for child in self.children:
            child.position.x = (child.position.x - self.position.x) * cos(angle) - (child.position.y - self.position.y) * sin(angle) + self.position.x
            child.position.y = (child.position.x - self.position.x) * sin(angle) + (child.position.y - self.position.y) * cos(angle) + self.position.y

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def remove_child(self, child):
        self.children.remove(child)
        child.parent = None
