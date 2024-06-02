import logging
import tkinter

from os import name as os_name

from library.config import AbstractConfig
from library.events import EventId, EventDispatcher
from library.model.control import InputUid
from library.resource_manager import ResourceManager
from library.time import Stopwatch


class AbstractCanvas:

    def __init__(self):
        pass

    def set_size(self, size):
        pass

    def set_background_color(self, color):
        pass


class AbstractWindow:

    def __init__(self):
        pass

    def set_title(self, title):
        pass

    def set_icon_path(self, image):
        pass

    def set_is_resizable(self, value):
        pass

    def create_canvas(self) -> AbstractCanvas:
        pass


class AbstractGraphics:

    def __init__(self):
        self._redraw_delay = 0
        self.tick_count = 0
        self._update_callback = None

    def world_space_to_screen_space(self, position):
        pass

    def screen_space_to_world_space(self, position):
        pass

    def create_window(self) -> AbstractWindow:
        pass

    def subscribe_on_update(self, callback):
        self._update_callback = callback

    def set_update_delay(self, delay_ms):
        self._redraw_delay = delay_ms

    def draw_image(self, image, position):
        pass

    def run(self):
        pass


class GraphicsTkinter(AbstractGraphics):

    def __init__(self, services):
        super().__init__()

        self._event_dispatcher = services[EventDispatcher]
        self._config = services[AbstractConfig]

        self._root = None

    def world_space_to_screen_space(self, position):
        return position * self._config['view']['px_per_unit'] * self._config['view']['scale']

    def screen_space_to_world_space(self, position):
        return position / self._config['view']['px_per_unit'] * self._config['view']['scale']

    def create_window(self):
        window = WindowTkinter(self)
        self._root = window._root
        return window

    def run(self):
        self._event_dispatcher.subscribe(EventId.DESTROY, self._on_destroy)
        self._root.after(self._redraw_delay, self._update)

        try:
            self._root.mainloop()
        except KeyboardInterrupt:
            self._on_destroy()

    def subscribe_on_key_press(self, callback):
        self._root.bind('<KeyPress>', callback)

    def subscribe_on_window_close(self, callback):
        self._root.protocol('WM_DELETE_WINDOW', callback)

    def _update(self):
        if self._update_callback:
            self._update_callback()

        self._root.after(self._redraw_delay, self._update)

    def _on_destroy(self, event_args=None):
        self._root.destroy()
        logging.info('App terminated')


class WindowTkinter(AbstractWindow):

    def __init__(self, graphics):
        super().__init__()

        self._graphics = graphics
        self._root = tkinter.Tk()

    def set_title(self, title):
        self._root.title(title)

    def set_icon_path(self, path):
        if os_name == 'nt':
            self._root.iconbitmap(bitmap=path)

    def set_is_resizable(self, value):
        self._root.resizable(value, value)

    def create_canvas(self) -> AbstractCanvas:
        return CanvasTkinter(self._root, self._graphics)


class CanvasTkinter(AbstractCanvas):

    def __init__(self, root, graphics):
        super().__init__()

        self._canvas = tkinter.Canvas(
            master=root,
            highlightthickness=0
        )
        self._canvas.pack(side='left')

        self._graphics = graphics

    def set_size(self, size):
        self._canvas.config(width=size.x, height=size.y)

    def set_background_color(self, color):
        self._canvas.configure(bg=color)

    def draw_line(self, from_, to, color):
        return self._canvas.create_line(
            from_.x, from_.y,
            to.x, to.y,
            fill=color
        )

    def draw_image(self, image, position):
        return self._canvas.create_image(
            position.x,
            position.y,
            image=image,
            anchor='nw'
        )

    def clear_all(self):
        self._canvas.delete('all')

    def clear(self, uid):
        self._canvas.delete(uid)


class Interface:

    def __init__(self, services):
        self._event_dispatcher = services[EventDispatcher]
        self._resources = services[ResourceManager]
        self._config = services[AbstractConfig]
        self._graphics = services[AbstractGraphics]
        # self._input_source = services[AbstractInputSource]

        self._window = self._graphics.create_window()
        app_name = self._config['interface']['app_name']
        version = self._config['interface']['version']
        self._window.set_title(app_name + ' v' + str(version))
        self._window.set_is_resizable(False)
        self._window.set_icon_path(self._resources.get_icon_path())

        self._canvas = self._window.create_canvas()
        self._canvas.set_background_color('#262626')

        self._graphics.set_update_delay(int(1000 / self._config['view']['fps']))
        self._graphics.subscribe_on_update(self._on_update)
        self.tick_count = 0
        self._step_by_step = self._config['debug']['is_debug'] and self._config['debug']['step_by_step']

    def _on_update(self):
        # if self._step_by_step and not self._input_source.is_pressed(InputUid.STEP):
        #     return

        stopwatch = Stopwatch()
        with stopwatch:
            for _ in range(8):
                self._event_dispatcher.fire(EventId.TICK, self, time=self.tick_count)
                self.tick_count += 1
            self._event_dispatcher.fire(EventId.REDRAW, self)
        # print(self.tick_count // 8)
        # if stopwatch.result_ms > 0:
            # print(1000 / stopwatch.result_ms)
        # else:
            # print('Inf')

    def get_canvas(self):
        return self._canvas

    def run(self):
        self._graphics.run()
