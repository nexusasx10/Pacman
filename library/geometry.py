import math
from enum import Enum

from library.utils import DataClass


class Vector(DataClass):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f'x={self.x}, y={self.y}'

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __mul__(self, number):
        return Vector(self.x * number, self.y * number)

    def distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def move(self, delta_x, delta_y):
        self.x += delta_x
        self.y += delta_y
        return self

    def shift(self, delta_x, delta_y):
        return Vector(self.x + delta_x, self.y + delta_y)

    def scale(self, other):
        return Vector(self.x * other.x, self.y * other.y)

    def with_(self, x=None, y=None):
        return Vector(
            x=x if x is not None else self.x,
            y=y if y is not None else self.y
        )


class Direction(Enum):
    EAST = 0
    NORTH = 90
    WEST = 180
    SOUTH = 270

    def is_oppositely(self, other):
        return abs(self.value - other.value) == 180

    def get_oppositely(self):
        return Direction((self.value + 180) % 360)

    def get_offset(self):
        return (
            int(math.cos(math.radians(self.value))),
            int(-math.sin(math.radians(self.value)))
        )
