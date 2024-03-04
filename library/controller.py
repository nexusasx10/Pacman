from enum import Enum

from library.config import Config
from library.events import EventId, EventDispatcher


class Control(Enum):
    UP = 0
    LEFT = 1
    DOWN = 2
    RIGHT = 3
    ENTER = 4
    EXIT = 5
    SAVE = 6


class InputSource:

    def __init__(self):
        pass

    def subscribe_input(self):
        pass


class Controller:

    def __init__(self, services, canvas):
        self._services = services
        self._event_dispatcher = self._services[EventDispatcher]
        self._canvas = canvas
        self._canvas._root.bind('<KeyPress>', self._on_key_press)
        self._canvas._root.protocol('WM_DELETE_WINDOW', self._on_stop)

    def _on_key_press(self, event):
        control = None
        if event.keysym.lower() in self._services[Config]['controls']:
            control = self._services[Config]['controls'][event.keysym.lower()]
        elif event.char.lower() in self._services[Config]['controls']:
            control = self._services[Config]['controls'][event.char.lower()]
        if control:
            control = control.upper()
            self._event_dispatcher.fire(EventId.CONTROL, self, value=Control[control])  # todo проверка на корректность config

    def _on_stop(self):
        self._event_dispatcher.fire(EventId.STOP, self)
