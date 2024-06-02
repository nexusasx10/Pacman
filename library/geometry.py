import math
from enum import Enum

from library.utils import value_or_default


class Vector2:

    __slots__ = ['x', 'y']

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f'x={self.x}, y={self.y}'

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return math.fabs(self.x - other.x) < 0.01 and math.fabs(self.y - other.y) < 0.01

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other):
        return type(self)(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return type(self)(self.x - other.x, self.y - other.y)

    def __mul__(self, number):
        return type(self)(self.x * number, self.y * number)

    def __truediv__(self, number):
        return type(self)(self.x / number, self.y / number)

    def __neg__(self):
        return type(self)(-self.x, -self.y)

    def __iter__(self):
        return iter((self.x, self.y))

    def distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def move(self, delta_x, delta_y):
        return type(self)(self.x + delta_x, self.y + delta_y)

    def scale(self, other):
        return type(self)(self.x * other.x, self.y * other.y)

    def rotate(self, angle, around=None):
        return type(self)(
            (self.x - around.x) * math.cos(angle) - (self.y - around.y) * math.sin(angle) + around.x,
            (self.x - around.x) * math.sin(angle) + (self.y - around.y) * math.cos(angle) + around.y
        )

    def with_(self, x=None, y=None):
        return type(self)(
            value_or_default(x, self.x),
            value_or_default(y, self.y)
        )

    @classmethod
    def zero(cls):
        return cls(0, 0)


class Direction(Enum):
    EAST = 0
    NORTH = 90
    WEST = 180
    SOUTH = 270

    def is_oppositely(self, other, epsilon=0.001):
        return abs(abs(self.value - other.value) - 180) < epsilon

    def get_oppositely(self):
        return Direction((self.value + 180) % 360)

    def to_vector(self):
        return Vector2(
            int(math.cos(math.radians(self.value))),
            int(-math.sin(math.radians(self.value)))
        )
