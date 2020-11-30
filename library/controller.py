from enum import Enum

from library.event import EventArgs, EventId


class Control(Enum):
    UP = 0
    LEFT = 1
    DOWN = 2
    RIGHT = 3
    ENTER = 4
    EXIT = 5
    SAVE = 6


class Controller:

    def __init__(self, services, root):
        self._services = services
        self._root = root
        self._root.bind('<KeyPress>', self._on_key_press)
        self._root.protocol('WM_DELETE_WINDOW', self._on_stop)

    def _on_key_press(self, event):
        control = None
        if event.keysym.lower() in self._services.config['controls']:
            control = self._services.config['controls'][event.keysym.lower()]
        elif event.char.lower() in self._services.config['controls']:
            control = self._services.config['controls'][event.char.lower()]
        if control:
            control = control.upper()
            self._services.event_dispatcher.fire(
                EventId.CONTROL, EventArgs(self, value=Control[control])  # todo проверка на корректность config
            )

    def _on_stop(self):
        self._services.event_dispatcher.fire(EventId.STOP, EventArgs(self))
