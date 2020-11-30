from itertools import chain


class Menu:

    def __init__(self):
        self.current_page = None
        self._history = []

    def enter(self):
        item = self.current_page.items[self.current_page.pointer]
        if item[3]:
            item[3]()
        if item[1]:
            new_page = item[1].enter()
            self._history.append(
                (self.current_page, self.current_page.pointer)
            )
            self.current_page = new_page
            self.current_page.reset()
        if not item[2]:
            self._history.clear()

    def back(self):
        if self._history:
            self.current_page, self.current_page.pointer = self._history.pop()

    def down(self):
        self.current_page.down()

    def up(self):
        self.current_page.up()

    def left(self):
        self.current_page.left()

    def right(self):
        self.current_page.right()


class PageItem:

    def __init__(self, title):
        self.title = title
        self.pointer = 0
        self.items = []
        self.cache = {}

    def add_item(self, caption, item, back, action=None):
        self.items.append((caption, item, back, action))

    def enter(self):
        return self

    def back(self):
        pass

    def down(self):
        if self.pointer < len(self.items) - 1:
            self.pointer += 1

    def up(self):
        if self.pointer > 0:
            self.pointer -= 1

    def left(self):
        pass

    def right(self):
        pass

    def reset(self):
        self.pointer = 0


class RatingsItem(PageItem):

    def __init__(self, services, title):
        super().__init__(title)
        self._services = services

    @property
    def ratings(self):
        return self._services.resources.list_ratings()


class SaveItem(PageItem):

    def __init__(self, services, title, save_func):
        super().__init__(title)
        self._services = services
        self._items = []
        self._save_func = save_func

    @property
    def items(self):
        return list(
            chain(
                (
                    (
                        str(i) + '. ' + s['info']['date'] if s else 'empty',
                        None,
                        True,
                        lambda i_=i: self._save_func(i_)
                    )
                    for i, s in self._services.resources.list_saves()
                ),
                self._items
            )
        )

    @items.setter
    def items(self, value):
        pass

    def add_item(self, caption, item, back, action=None):
        self._items.append((caption, item, back, action))


class LoadItem(PageItem):

    def __init__(self, services, title, load_func):
        super().__init__(title)
        self._services = services
        self._items = []
        self._load_func = load_func

    @property
    def items(self):
        return list(
            chain(
                (
                    (
                        save['info']['date'],
                        None,
                        False,
                        lambda idx=index: self._load_func(idx)
                    )
                    for index, save in self._services.resources.list_saves()
                    if save
                ),
                self._items
            )
        )

    @items.setter
    def items(self, value):
        pass

    def add_item(self, caption, item, back, action=None):
        self._items.append((caption, item, back, action))


class RecordItem(PageItem):

    def __init__(self, services, title):
        super().__init__(title)
        self._services = services
        self.char_pointer = 0
        max_name_length = self._services.config['common']['max_name_length']
        self.cache['name'] = [0] * max_name_length

    def up(self):
        if self.char_pointer == len(self.cache['name']):
            super().up()
            return
        if self.cache['name'][self.char_pointer] > 0:
            self.cache['name'][self.char_pointer] -= 1

    def down(self):
        if self.char_pointer == len(self.cache['name']):
            super().down()
            return
        symbol_count = len(self._services.config['model']['symbols'])
        if self.cache['name'][self.char_pointer] < symbol_count - 1:
            self.cache['name'][self.char_pointer] += 1

    def right(self):
        if self.char_pointer < len(self.cache['name']):
            self.char_pointer += 1

    def left(self):
        if self.char_pointer > 0:
            self.char_pointer -= 1

    def reset(self):
        super().reset()
        self.char_pointer = 0
        max_name_length = self._services.config['common']['max_name_length']
        self.cache['name'] = [0] * max_name_length
