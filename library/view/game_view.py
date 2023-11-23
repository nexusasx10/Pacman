from collections import deque

from library.event import EventId
from library.geometry import Vector, Direction
from library.graphics import AnimationDrawer
from library.interface import Interface
from library.model.actor import Pacman, Enemy
from library.model.field import Block, Grid
from library.model.game_driver import GameDriver
from library.model.menu import RatingsItem, RecordItem


class TextDrawer:

    class Align:
        LEFT = 0
        CENTER = 1
        RIGHT = 2

    _offset = Vector(-8, -8)

    def __init__(self, services, canvas):
        self._services = services
        self._canvas = canvas
        self._drawers = []

    def draw(self, position, text, align=Align.CENTER):
        if align == self.Align.RIGHT:
            position = position.shift(-len(text), 0)
        elif align == self.Align.CENTER:
            position = position.shift(-len(text) / 2, 0)
        self.clear()
        for i, char in enumerate(text):
            if char == ' ':
                continue
            drawer = AnimationDrawer(self._services, self._canvas)
            self._drawers.append(drawer)
            drawer.draw(
                position.shift(i, 0),
                self._offset,
                'char',
                char
            )

    def clear(self):
        while self._drawers:
            drawer = self._drawers.pop()
            drawer.clear()


class ActorDrawer:

    _offset = Vector(-16, -16)

    def __init__(self, services, canvas):
        self._drawer = AnimationDrawer(services, canvas)

    def draw(self, actor, animation_name):
        self._drawer.draw(
            actor.position,
            self._offset,
            actor.name,
            animation_name
        )

    def clear(self):
        self._drawer.clear()


class PacmanDrawer:

    def __init__(self, services, canvas):
        self._drawer = ActorDrawer(services, canvas)

    def draw(self, actor):
        if actor.mode[0] == Pacman.Mode.DEAD:
            self._drawer.draw(actor, 'dead')
        elif actor.mode[1] == Pacman.Mode.WAITING:
            self._drawer.draw(actor, 'waiting_' + actor.direction.name.lower())
        elif actor.mode[1] == Pacman.Mode.WALKING:
            self._drawer.draw(actor, 'walking_' + actor.direction.name.lower())

    def clear(self):
        self._drawer.clear()


class EnemyDrawer:

    def __init__(self, services, canvas):
        self._drawer = ActorDrawer(services, canvas)

    def draw(self, actor):
        if actor.mode[0] == Enemy.Mode.NONE:
            self._drawer.draw(actor, actor.direction.name.lower())
        elif actor.mode[0] == Enemy.Mode.FRIGHTENED:
            self._drawer.draw(actor, 'frightened')
        elif actor.mode[0] == Enemy.Mode.FRIGHTENED_END:
            self._drawer.draw(actor, 'frightened_end')
        elif actor.mode[0] == Enemy.Mode.DEAD:
            self._drawer.draw(actor, 'dead_' + actor.direction.name.lower())

    def clear(self):
        self._drawer.clear()


class BlockDrawer:

    _offset = Vector(-8, -8)

    def __init__(self, services, canvas):
        self._drawer = AnimationDrawer(services, canvas)
        self._last_state = None

    def draw(self, block, field):
        # if not self._last_state:  # todo
        #     self._last_state = 1
        # elif self._last_state == block.content:
        #     return
        # else:
        #     self._last_state = block.content
        if block.content == Block.Content.FRUIT:
            self._drawer.draw(
                block.cell,
                self._offset,
                'block',
                'fruit_0'
            )
        elif block.content == Block.Content.WALL:
            self._drawer.draw(
                block.cell,
                self._offset,
                'block',
                'wall_' + str(self.wall_type(block, field))
            )
        else:
            self._drawer.draw(
                block.cell,
                self._offset,
                'block',
                block.content.name.lower()
            )

    @staticmethod
    def wall_type(block, field):
        e_point = field.grid.anchors['enemies']
        if e_point.x < block.cell.x < e_point.x + 7:
            if block.cell.y == e_point.y:
                return 2
            if block.cell.y == e_point.y + 4:
                return 8
        if e_point.y < block.cell.y < e_point.y + 4:
            if block.cell.x == e_point.x:
                return 4
            if block.cell.x == e_point.x + 7:
                return 6
        if list(block.connections.values()).count(True) == 0:
            up = field.grid[block.cell.shift(0, -1)]
            down = field.grid[block.cell.shift(0, 1)]
            if up.connections[Direction.WEST]:
                return 13
            elif up.connections[Direction.EAST]:
                return 12
            elif down.connections[Direction.WEST]:
                return 11
            elif down.connections[Direction.EAST]:
                return 10
            else:
                return 5
        else:
            conf = {
                0: 6, 90: 2, 180: 4, 270: 8, 360: 3, 810: 1, 1080: 9, 1260: 7
            }
            sum_ = sum(
                map(
                    lambda x: (x[0] * 3 + 1) * x[1],
                    enumerate(
                        sorted(
                            map(
                                lambda x: x.value,
                                filter(
                                    lambda x: block.connections[x],
                                    block.connections
                                )
                            )
                        )
                    )
                )
            )
            return conf[sum_]

    def clear(self):
        self._drawer.clear()


class BackgroundDrawer:

    _offset = Vector(-8, -8)

    def __init__(self, services, canvas, size):
        self._services = services
        self._canvas = canvas
        self._size = size
        self._drawers = {}
        for i in range(Interface.default_size.x):
            for j in range(Interface.default_size.y):
                self._drawers[i, j] = AnimationDrawer(services, canvas)

    def draw(self, position):
        for j in range(self._size.y):
            for i in range(self._size.x):
                args = (position.shift(i, j), self._offset, 'block')
                if j == 0:
                    if i == 0:
                        self._drawers[i, j].draw(*args, 'wall_10')
                    elif i == self._size.x - 1:
                        self._drawers[i, j].draw(*args, 'wall_11')
                    else:
                        self._drawers[i, j].draw(*args, 'wall_8')
                elif j == self._size.y - 1:
                    if i == 0:
                        self._drawers[i, j].draw(*args, 'wall_12')
                    elif i == self._size.x - 1:
                        self._drawers[i, j].draw(*args, 'wall_13')
                    else:
                        self._drawers[i, j].draw(*args, 'wall_2')
                else:
                    if i == 0:
                        self._drawers[i, j].draw(*args, 'wall_6')
                    elif i == self._size.x - 1:
                        self._drawers[i, j].draw(*args, 'wall_4')
                    else:
                        self._drawers[i, j].draw(*args, 'empty')


class MenuDrawer:

    _offset = Vector(-8, -8)

    def __init__(self, services, canvas):
        self._services = services
        self._canvas = canvas
        self._title_drawer = TextDrawer(self._services, self._canvas)
        self._content_drawers = []
        self._background_drawer = BackgroundDrawer(
            self._services, self._canvas, Interface.default_size
        )

    def initial_draw(self, model):
        self._canvas.set_size(Interface.default_size.scale(Block.size))
        self._background_drawer.draw(Vector(0, 0))

    def _draw_content(self, content):
        while self._content_drawers:
            drawer = self._content_drawers.pop()
            drawer.clear()
        for i, line in enumerate(content):
            x = Interface.default_size.x / 2
            y = (Interface.default_size.y - len(content)) / 2 + i
            drawer = TextDrawer(self._services, self._canvas)
            self._content_drawers.append(drawer)
            drawer.draw(Vector(x, y), line)

    def _draw_page(self, menu, prev_content):
        for i, (caption, _, _, _) in enumerate(menu.current_page.items):
            if i == menu.current_page.pointer:
                prev_content.append('> ' + caption + '  ')
            else:
                prev_content.append(caption)
        self._draw_content(prev_content)

    def _draw_ratings(self, menu, prev_content):
        for i, (name, rating) in enumerate(menu.current_page.ratings):
            space = '.' * (16 - (len(name) + len(str(rating))))
            prev_content.append(str(i + 1) + '.' + name + space + str(rating))
        prev_content.append('')
        self._draw_page(menu, prev_content)

    def _draw_record(self, menu, prev_content):
        first = ''
        second = ''
        third = ''
        for i, p in enumerate(menu.current_page.cache['name']):
            first += '^' if menu.current_page.char_pointer == i else ' '
            second += self._services.config['model']['symbols'][p]
            third += '`' if menu.current_page.char_pointer == i else ' '
        prev_content.append(first)
        prev_content.append(second)
        prev_content.append(third)
        prev_content.append('')
        self._draw_page(menu, prev_content)

    def draw(self, model):
        if not model:
            return
        x = Interface.default_size.x / 2
        y = Interface.default_size.y / 4
        self._title_drawer.draw(Vector(x, y), model.menu.current_page.title)
        if type(model.menu.current_page) == RatingsItem:
            self._draw_ratings(model.menu, [])
        elif type(model.menu.current_page) == RecordItem:
            self._draw_record(model.menu, [])
        else:
            self._draw_page(model.menu, [])

    def clear(self):  # todo
        pass


class GameDrawer:

    def __init__(self, services, canvas):
        self._services = services
        self._canvas = canvas
        self._actor_drawers = {}
        self._block_drawers = {}
        self._text_drawer = TextDrawer(self._services, self._canvas)
        self._actor_drawers['pacman'] = PacmanDrawer(
            self._services,
            self._canvas
        )
        self._actor_drawers['red_ghost'] = EnemyDrawer(
            self._services,
            self._canvas
        )
        self._actor_drawers['pink_ghost'] = EnemyDrawer(
            self._services,
            self._canvas
        )
        self._actor_drawers['blue_ghost'] = EnemyDrawer(
            self._services,
            self._canvas
        )
        self._actor_drawers['orange_ghost'] = EnemyDrawer(
            self._services,
            self._canvas
        )
        self._level_drawers = TextDrawer(services, self._canvas)
        self._scores_drawers = TextDrawer(services, self._canvas)
        self._lives_drawers = TextDrawer(services, self._canvas)
        self._background_drawer = None

    def initial_draw(self, model):
        self._canvas.set_size((model.field.grid.size + Vector(16, 0)).scale(Block.size))
        for x in range(model.field.grid.size.x):
            for y in range(model.field.grid.size.y):
                self._block_drawers[Vector(x, y)] = BlockDrawer(
                    self._services,
                    self._canvas
                )
        self._background_drawer = BackgroundDrawer(
            self._services, self._canvas, model.field.grid.size.with_(x=16)
        )
        self._background_drawer.draw(model.field.grid.size.with_(y=0))

    def draw(self, model):
        if not model:
            return
        for block in model.field.grid:
            self._block_drawers[block.cell].draw(block, model.field)
        for actor in model.field.actors.values():
            self._actor_drawers[actor.name].draw(actor)
        self._level_drawers.draw(
            Vector(model.field.grid.size.x + 1, 1),
            'level: {}'.format(model.level),
            TextDrawer.Align.LEFT
        )
        self._scores_drawers.draw(
            Vector(model.field.grid.size.x + 1, 3),
            'scores: {}'.format(model.scores),
            TextDrawer.Align.LEFT
        )
        self._lives_drawers.draw(
            Vector(model.field.grid.size.x + 1, 5),
            'lives: {}'.format(model.lives),
            TextDrawer.Align.LEFT
        )


class WinDrawer:

    def __init__(self, services, canvas):
        self._services = services
        self._canvas = canvas
        self._background_drawer = BackgroundDrawer(
            self._services, self._canvas, Interface.default_size
        )
        self._text_drawer = TextDrawer(self._services, self._canvas)

    def draw(self, model):
        self._background_drawer.draw(Vector(0, 0))
        x = Interface.size.x / 2
        y = Interface.size.y / 2
        self._text_drawer.draw(Vector(x, y), 'you win!')


class LoseDrawer:

    def __init__(self, services, canvas):
        self._services = services
        self._canvas = canvas
        self._background_drawer = BackgroundDrawer(
            services, canvas, Interface.default_size
        )
        self._text_drawer = TextDrawer(services, self._canvas)

    def draw(self, model):
        self._background_drawer.draw(Vector(0, 0))
        x = Interface.size.x / 2
        y = Interface.size.y / 2
        self._text_drawer.draw(Vector(x, y), 'you lose...')


class View:

    def __init__(self, services, canvas):
        self._services = services
        self._canvas = canvas
        self._model = None
        self._old_mode = None
        self._mode_change = deque()
        self._drawers = {
            GameDriver.Mode.PLAY: GameDrawer(self._services, self._canvas),
            GameDriver.Mode.FREE: GameDrawer(self._services, self._canvas),
            GameDriver.Mode.MENU: MenuDrawer(self._services, self._canvas),
            GameDriver.Mode.WIN: WinDrawer(self._services, self._canvas),
            GameDriver.Mode.LOSE: LoseDrawer(self._services, self._canvas)
        }
        self._services.event_dispatcher.subscribe(EventId.MODEL_UPDATE, self._on_model_update)
        self._services.event_dispatcher.subscribe(EventId.REDRAW, self._on_redraw)

    def _on_model_update(self, event_args):
        self._model = event_args.model
        if self._old_mode != self._model.mode:
            self._mode_change.append((self._old_mode, self._model.mode))
        self._old_mode = self._model.mode

    def _on_redraw(self, event_args):
        if not self._model:
            return
        if self._mode_change:
            self._canvas.clear_all()
            old, new = self._mode_change.popleft()
            if new == GameDriver.Mode.MENU:
                self._drawers[GameDriver.Mode.MENU].initial_draw(self._model)
            elif new == GameDriver.Mode.PLAY:
                self._drawers[GameDriver.Mode.PLAY].initial_draw(self._model)
            if new == GameDriver.Mode.WAIT:
                self._drawers[GameDriver.Mode.PLAY].initial_draw(self._model)
                self._drawers[GameDriver.Mode.PLAY].draw(self._model)
        if self._model.mode in self._drawers:
            self._drawers[self._model.mode].draw(self._model)
        # todo отрисовывать акторов, только когда они в пределах видимой
        # todo области иначе обрезать
