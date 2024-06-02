from math import cos, sin

from engine.component_alias import component_alias
from engine.components import Component
from library.geometry import Vector2
from library.utils import value_or_default


class Transform2:

    def __init__(self, parent=None, position=None, rotation=None):
        self.position = value_or_default(position, Vector2.zero())
        self.rotation = value_or_default(rotation, 0)
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

    def find_child(self, name):
        for child in self.children:
            if child.name == name:
                return child


@component_alias('transform')
class Transform2Component(Component):

    def __init__(self, owner):
        super().__init__(owner)
        self._transform = Transform2()

    def move(self, offset):
        self._transform.move(offset)

    def rotate(self, angle):
        self._transform.rotate(angle)

    def add_child(self, child):
        self._transform.add_child(child)

    def remove_child(self, child):
        self._transform.remove_child(child)

    def find_child(self, name):
        self._transform.find_child(name)
