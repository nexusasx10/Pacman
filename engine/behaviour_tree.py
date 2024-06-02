class BehaviourTree:

    def __init__(self):
        self._root = BehaviourNode()

    def update(self):
        self._root.update()


class BehaviourNode:
    pass


class Selector:
    pass


class Sequence:
    pass
