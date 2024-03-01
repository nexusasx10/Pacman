import logging
import tkinter

from os import name as os_name

from library.config import Config
from library.event import EventId, EventDispatcher
from library.geometry import Vector
from library.resource_manager import ResourceManager
from library.time import Stopwatch


class Canvas:

    def __init__(self):
        pass

    def set_title(self, title):
        pass

    def set_icon_path(self, image):
        pass

    def set_size(self, size):
        pass

    def set_is_resizable(self, value):
        pass

    def set_background_color(self, color):
        pass


class Graphics:

    def __init__(self, services):
        self._services = services

        self._redraw_delay = 0
        self.tick_count = 0
        self._update_callback = None

    def world_space_to_screen_space(self, position):
        pass

    def screen_space_to_world_space(self, position):
        pass

    def create_canvas(self) -> Canvas:
        pass

    def subscribe_on_update(self, callback):
        self._update_callback = callback

    def set_update_delay(self, delay_ms):
        self._redraw_delay = delay_ms

    def draw_image(self, image, position):
        pass

    def run(self):
        pass


class GraphicsTkinter(Graphics):

    def __init__(self, services):
        super().__init__(services)

        self._root = None

    def world_space_to_screen_space(self, position):
        return position * self._services[Config]['view']['px_per_unit']

    def screen_space_to_world_space(self, position):
        return position / self._services[Config]['view']['px_per_unit']

    def create_canvas(self):
        self._root = tkinter.Tk()
        return CanvasTkinter(self, self._root)

    def run(self):
        self._services[EventDispatcher].subscribe(EventId.DESTROY, self._on_destroy)
        self._root.after(self._redraw_delay, self._update)

        try:
            self._root.mainloop()
        except KeyboardInterrupt:
            self._on_destroy()

    def _update(self):
        if self._update_callback:
            self._update_callback()

        self._root.after(self._redraw_delay, self._update)

    def _on_destroy(self, event_args=None):
        self._root.destroy()
        logging.info('App terminated')


class CanvasTkinter(Canvas):

    def __init__(self, graphics, root):
        super().__init__()

        self._graphics = graphics
        self._root = root
        self._root.canvas = tkinter.Canvas(
            master=self._root,
            highlightthickness=0
        )
        self._root.canvas.pack(side='left')

    def set_title(self, title):
        self._root.title(title)

    def set_icon_path(self, path):
        if os_name == 'nt':
            self._root.iconbitmap(bitmap=path)

    def set_size(self, size):
        self._root.canvas.config(width=size.x, height=size.y)

    def set_is_resizable(self, value):
        self._root.resizable(value, value)

    def set_background_color(self, color):
        self._root.canvas.configure(bg=color)

    def draw_line(self, from_, to, color):
        return self._root.canvas.create_line(
            from_.x, from_.y,
            to.x, to.y,
            fill=color
        )

    def draw_image(self, image, position):
        return self._root.canvas.create_image(
            position.x,
            position.y,
            image=image,
            anchor='nw'
        )

    def clear_all(self):
        self._root.canvas.delete('all')

    def clear(self, uid):
        self._root.canvas.delete(uid)


class Interface:

    def __init__(self, services, graphics: Graphics):
        self._event_dispatcher = services[EventDispatcher]
        self._resources = services[ResourceManager]
        self._config = services[Config]
        self._graphics = graphics

        self._canvas = self._graphics.create_canvas()
        app_name = self._config['interface']['app_name']
        version = self._config['interface']['version']
        self._canvas.set_title(app_name + ' v' + str(version))
        self._canvas.set_is_resizable(False)
        self._canvas.set_icon_path(self._resources.get_icon_path())
        self._canvas.set_background_color('#262626')

        self._graphics.set_update_delay(int(1000 / self._config['view']['fps']))
        self._graphics.subscribe_on_update(self._on_update)
        self.tick_count = 0

    def _on_update(self):
        stopwatch = Stopwatch()
        with stopwatch:
            for _ in range(8):
                self._event_dispatcher.fire(EventId.TICK, self, time=self.tick_count)
                self.tick_count += 1
            self._event_dispatcher.fire(EventId.REDRAW, self)
        print(self.tick_count // 8)
        # if stopwatch.result_ms > 0:
            # print(1000 / stopwatch.result_ms)
        # else:
            # print('Inf')

    def get_canvas(self):
        return self._canvas

    def run(self):
        self._graphics.run()
