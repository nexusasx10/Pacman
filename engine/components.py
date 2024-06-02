

class Component:

    def __init__(self, owner):
        # todo weak ref or custom destroy method
        self._owner = owner

    def __repr__(self):
        return f'{type(self).__name__} component of {self._owner}'

    def owner(self):
        return self._owner
