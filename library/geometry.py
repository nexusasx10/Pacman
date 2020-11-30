import math
from enum import Enum

from library.utils import DataClass


class Point(DataClass):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return '{},{}'.format(self.x, self.y)

    def distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def move(self, delta_x, delta_y):
        self.x += delta_x
        self.y += delta_y
        return self

    def shift(self, delta_x, delta_y):
        return Point(self.x + delta_x, self.y + delta_y)


class Size(DataClass):
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def __repr__(self):
        return '{},{}'.format(self.width, self.height)

    def __mul__(self, number):
        return Size(int(self.width * number), int(self.height * number))


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
