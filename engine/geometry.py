

class Vector2:

    _zero = None
    _right = None
    _up = None

    @classmethod
    def zero(cls):
        if cls._zero is None:
            cls._zero = Vector2(0, 0)

        return cls._zero

    @classmethod
    def right(cls):
        if cls._right is None:
            cls._right = Vector2(1, 0)

        return cls._right

    @classmethod
    def up(cls):
        if cls._up is None:
            cls._up = Vector2(0, 1)

        return cls._up

    __slots__ = '_x', '_y'

    def __init__(self, x: float, y: float):
        self._x: float = x
        self._y: float = y

    def __repr__(self):
        return f'({self._x}, {self._y})'

    def x(self) -> float:
        return self._x

    def y(self) -> float:
        return self._y

    def magnitude(self):
        return (self._x ** 2 + self._y ** 2) ** 0.5

    def distance(self, another):
        return ((self._x - another.x) ** 2 + (self._y - another.y) ** 2) ** 0.5

    def cast(self, type_):
        if type_ == Vector2:
            return self

        if type_ == Vector3:
            return Vector3(self._x, self._y, 0)

        raise ValueError(f'Can\'t cast to {type_}.')


class Vector3(Vector2):

    _zero = None
    _right = None
    _up = None
    _forward = None

    @classmethod
    def zero(cls):
        if cls._zero is None:
            cls._zero = Vector3(0, 0, 0)

        return cls._zero

    @classmethod
    def right(cls):
        if cls._right is None:
            cls._right = Vector3(1, 0, 0)

        return cls._right

    @classmethod
    def up(cls):
        if cls._up is None:
            cls._up = Vector3(0, 1, 0)

        return cls._up

    @classmethod
    def forward(cls):
        if cls._forward is None:
            cls._forward = Vector3(0, 0, 1)

    __slots__ = '_z'

    def __init__(self, x: float, y: float, z: float):
        super().__init__(x, y)
        self._z: float = z

    def __repr__(self):
        return f'({self._x}, {self._y}, {self._z})'

    def z(self) -> float:
        return self._z

    def magnitude(self):
        return (self._x ** 2 + self._y ** 2 + self._z ** 2) ** 0.5

    def distance(self, another):
        return ((self._x - another.x) ** 2 + (self._y - another.y) ** 2 + (self._z - another.z) ** 2) ** 0.5


class Matrix3x3:

    _identity = None

    @classmethod
    def identity(cls):
        if cls._identity is None:
            cls._identity = Matrix3x3(
                1, 0, 0,
                0, 1, 0,
                0, 0, 1
            )

        return cls._identity

    __slots__ = '_m00', '_m01', '_m02', '_m10', '_m11', '_m12', '_m20', '_m21', '_m22',

    def __init__(self, m00, m01, m02, m10, m11, m12, m20, m21, m22):
        self._m00 = m00
        self._m01 = m01
        self._m02 = m02
        self._m10 = m10
        self._m11 = m11
        self._m12 = m12
        self._m20 = m20
        self._m21 = m21
        self._m22 = m22

    def get_row(self, i):
        if i == 0:
            return Vector3(self._m00, self._m01, self._m02)
        elif i == 1:
            return Vector3(self._m10, self._m11, self._m12)
        elif i == 2:
            return Vector3(self._m20, self._m21, self._m22)
        else:
            raise ValueError()

    def get_column(self, j):
        if j == 0:
            return Vector3(self._m00, self._m10, self._m20)
        elif j == 1:
            return Vector3(self._m01, self._m11, self._m21)
        elif j == 2:
            return Vector3(self._m02, self._m12, self._m22)
        else:
            raise ValueError()

# todo а точно так переводится?
    def transpose(self):
        return Matrix3x3(
            self._m00, self._m10, self._m20,
            self._m01, self._m11, self._m21,
            self._m02, self._m12, self._m22
        )
