import logging
import tkinter
from os import name as os_name

from library.event import EventArgs, EventId
from library.geometry import Size
from library.model.field import Block
from library.time import Stopwatch


class Interface:

    size = Size(44, 31)

    def __init__(self, services):
        self._services = services
        self.root = tkinter.Tk()
        root_title = self._services.config['interface']['root_title']
        version = self._services.config['interface']['version']
        self.root.title(root_title + ' v' + str(version))
        self.root.resizable(False, False)
        if os_name == 'nt':
            self.root.iconbitmap(bitmap=self._services.resources.get_icon())
        self.root.display = tkinter.Canvas(
            bg='#262626',
            master=self.root,
            highlightthickness=0
        )
        self.root.display.config(
            width=self.size.width * Block.size.width,
            height=self.size.height * Block.size.height
        )
        self.root.display.pack(side='left')
        self._redraw_delay = int(1000 / self._services.config['view']['fps'])
        self._services.event_dispatcher.subscribe(EventId.DESTROY, self._on_destroy)
        self.tick_count = 0
        self.root.after(self._redraw_delay, self._on_update)

    def _on_update(self):
        stopwatch = Stopwatch()
        with stopwatch:
            for _ in range(8):
                self._services.event_dispatcher.fire(EventId.TICK, self, time=self.tick_count)
                self.tick_count += 1
            self._services.event_dispatcher.fire(EventId.REDRAW, self)
        print(self.tick_count // 8)
        # if stopwatch.result_ms > 0:
            # print(1000 / stopwatch.result_ms)
        # else:
            # print('Inf')
        self.root.after(self._redraw_delay, self._on_update)

    def _on_destroy(self, event_args=None):
        self.root.destroy()
        logging.info('App terminated')

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_destroy()
