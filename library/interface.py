import logging
import tkinter
from os import name as os_name

from library.event import EventArgs, EventId
from library.geometry import Size
from library.model.field import Block


class Interface:

    size = Size(44, 31)

    def __init__(self, services):
        self._services = services
        self.root = tkinter.Tk()
        self.root.title(self._services.config['interface']['root_title'])
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
        self._services.event_dispatcher.register_handler(
            EventId.DESTROY, self._on_destroy
        )
        self.root.after(self._redraw_delay, self._on_update)

    def _on_update(self):
        self._services.event_dispatcher.fire(EventId.REDRAW, EventArgs(self))
        self.root.after(self._redraw_delay, self._on_update)

    def _on_destroy(self, event_args):
        self.root.destroy()
        logging.info('App terminated')

    def run(self):
        self.root.mainloop()
