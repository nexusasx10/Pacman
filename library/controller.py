from library.config import AbstractConfig
from library.events import EventId, EventDispatcher
from library.interface import AbstractGraphics
from library.model.control import InputUid


class AbstractInputSource:

    def subscribe_input(self):
        pass


class InputSourceTkinter(AbstractInputSource):

    def __init__(self, services):
        self._controls = services[AbstractConfig]['controls']
        self._event_dispatcher = services[EventDispatcher]
        self._graphics = services[AbstractGraphics]
        self._graphics.subscribe_on_key_press(self._on_key_press)
        self._graphics.subscribe_on_window_close(self._on_stop)
        self._event_dispatcher.subscribe(EventId.MODEL_UPDATE, self._handle_update)
        self._pressed = []

    def is_pressed(self, control):
        return control in self._pressed

    def _handle_update(self, t):
        self._pressed.clear()

    def _on_key_press(self, event):
        raw_input = None
        if event.keysym.lower() in self._controls:
            raw_input = self._controls[event.keysym.lower()]
        elif event.char.lower() in self._controls:
            raw_input = self._controls[event.char.lower()]
        if raw_input:
            raw_input = raw_input.upper()
            input_uid = InputUid[raw_input]
            self._pressed.append(input_uid)
            self._event_dispatcher.fire(EventId.CONTROL, self, value=input_uid)  # todo проверка на корректность config

    def _on_stop(self):
        self._event_dispatcher.fire(EventId.STOP, self)
