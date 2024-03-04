from collections import defaultdict, deque
from enum import Enum


class EventDispatcher:

    def __init__(self):
        self._handlers = defaultdict(list)

    def subscribe(self, event_id, handler, priority=0):
        self._handlers[event_id].append((priority, handler))
        # сортируем по приоритету
        self._handlers[event_id].sort(key=lambda x: x[0])

    def unsubscribe(self, event_id, handler, priority=0):  # TODO: Remove priority
        self._handlers[event_id].remove((priority, handler))

    def fire(self, event_id, sender, **kwargs):
        for _, handler in self._handlers[event_id]:
            event_args = EventArgs(sender, **kwargs)
            handler(event_args)


class EventArgs:

    def __init__(self, sender, **kwargs):
        self.sender = sender
        self.__dict__.update(kwargs)


class EventId(Enum):
    TICK = 0
    CONTROL = 1
    STOP = 2
    DESTROY = 3
    MODEL_UPDATE = 4
    GAME_INIT = 21
    GAME_START = 5
    GAME_RESTART = 6
    GAME_END = 7
    NEXT_LEVEL = 22
    PINK_GHOST_OUT = 8
    BLUE_GHOST_OUT = 9
    ORANGE_GHOST_OUT = 10
    GHOST_BEHIND_DOOR = 11
    GHOST_ON_DEAD_TARGET = 12
    SWITCH_TIMEOUT = 13
    MODE_CHANGE = 14
    INTERSECTION = 15
    PICKUP = 16
    CROSSWAY = 17
    FRIGHTENED_TIMEOUT = 18
    ENERGIZER_TIMEOUT = 19
    REDRAW = 20
