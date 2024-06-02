from collections import deque

from library.config import AbstractConfig
from library.events import EventId, EventDispatcher
from library.geometry import Vector2, Direction
from library.graphics import SpriteDrawer
from library.interface import AbstractGraphics
from library.model.actor import Pacman, Enemy, Actor
from library.model.field import Block
from library.model.game_driver import GameDriver
from library.model.menu import RatingsItem, RecordItem
from library.resource_manager import ResourceManager


class TextDrawer:

    class Align:
        LEFT = 0
        CENTER = 1
        RIGHT = 2

    _offset = Block.size / 2

    def __init__(self, services, canvas):
        self._services = services
        self._sprite = self._services[ResourceManager].get_sprite('symbols')
        self._canvas = canvas
        self._drawers = []

    def draw(self, position, text, align=Align.CENTER):
        if align == self.Align.RIGHT:
            position = position.move(-len(text), 0)
        elif align == self.Align.CENTER:
            position = position.move(-len(text) / 2, 0)
        self.clear()
        for i, char in enumerate(text):
            if char == ' ':
                continue
            drawer = SpriteDrawer(self._services[AbstractGraphics], self._canvas)  # todo: why we are creating it each frame?
            self._drawers.append(drawer)
            idx = self._services[ResourceManager].get_symbol_map()[ord(char)]
            drawer.draw(position.move(i, 0) + self._offset, self._sprite, idx)

    def clear(self):
        while self._drawers:
            drawer = self._drawers.pop()
            drawer.clear()


class ActorDrawer:

    _offset = -Actor.size / 2

    def __init__(self, resources, graphics, canvas):
        self._color = (255, 0, 0)
        self._sprite_drawer = SpriteDrawer(graphics, canvas)
        self._resources = resources

    def draw(self, actor, sprite_uid, color=None):
        sprite_file = self._resources.get_sprite_library()[sprite_uid]['file']
        sprite = self._resources.get_sprite(sprite_file, color)
        self._sprite_drawer.draw(
            actor.position + self._offset,
            sprite,
            actor.sprite_idx
        )

    def clear(self):
        self._sprite_drawer.clear()


class PacmanDrawer:

    _actor_name = 'pacman'

    def __init__(self, graphics, canvas, resources):
        self._resources = resources
        animation = self._resources.get_animation(self._actor_name)
        self._animation_context = animation.create_context()
        self._actor_drawer = ActorDrawer(self._resources, graphics, canvas)

    def draw(self, actor):
        animation_name = f'{self._actor_name}/'
        match actor.mode:
            case (Pacman.Mode.DEAD, _):
                animation_name += 'dead'
            case (_, Pacman.Mode.WAITING):
                animation_name += f'waiting_{actor.direction.name.lower()}'
            case (_, Pacman.Mode.WALKING):
                animation_name += f'walking_{actor.direction.name.lower()}'
        self._animation_context.time += 0.06
        self._animation_context.update(actor)
        self._actor_drawer.draw(actor, self._actor_name)

    def clear(self):
        self._actor_drawer.clear()


class EnemyDrawer:

    _base_actor_name = 'ghost'

    def __init__(self, graphics, canvas, resources, actor_name, color):
        self._resources = resources
        self._actor_name = actor_name
        self._color = color
        self._drawer = ActorDrawer(self._resources, graphics, canvas)
        animation = self._resources.get_animation(self._base_actor_name)
        self._animation_context = animation.create_context()

    def draw(self, actor):
        animation_name = f'{self._actor_name}/'
        match actor.mode[0]:
            case Enemy.Mode.NONE:
                animation_name += actor.direction.name.lower()
            case Enemy.Mode.FRIGHTENED:
                animation_name += 'frightened'
            case Enemy.Mode.FRIGHTENED_END:
                animation_name += 'frightened_end'
            case Enemy.Mode.DEAD:
                animation_name += f'dead_{actor.direction.name.lower()}'
        self._animation_context.time += 0.06
        self._animation_context.update(actor)
        self._drawer.draw(actor, self._base_actor_name, self._color)

    def clear(self):
        self._drawer.clear()


class BlockDrawer:

    _offset = -Block.size / 2

    def __init__(self, services, canvas):
        self._resources = services[ResourceManager]
        self._drawer = SpriteDrawer(services[AbstractGraphics], canvas)
        self._last_state = None

    def draw(self, block, field):
        # if not self._last_state:  # todo
        #     self._last_state = 1
        # elif self._last_state == block.content:
        #     return
        # else:
        #     self._last_state = block.content
        sprite_name = ''
        match block.content:
            case Block.Content.FRUIT:
                sprite_name += 'fruit_0'
            case Block.Content.WALL:
                sprite_name += f'wall_{self.wall_type(block, field)}'
            case _:
                sprite_name += block.content.name.lower()
        sprite_data = self._resources.get_sprite_library()[sprite_name]
        sprite = self._resources.get_sprite(sprite_data['file'])
        idx = sprite_data['default_idx']
        self._drawer.draw(block.cell + self._offset, sprite, idx)

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
            up = field.grid[block.cell.move(0, -1)]
            down = field.grid[block.cell.move(0, 1)]
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

    _offset = -Block.size / 2

    def __init__(self, services, canvas):
        self._config = services[AbstractConfig]
        self._sprite = services[ResourceManager].get_sprite('block')
        self._graphics = services[AbstractGraphics]
        self._resources = services[ResourceManager]
        self._canvas = canvas
        self._drawers = {}

    def _get_drawer(self, i, j):
        if (i, j) not in self._drawers:
            self._drawers[i, j] = SpriteDrawer(self._graphics, self._canvas)
        return self._drawers[i, j]

    def draw(self, position, size):
        for j in range(size.y):
            for i in range(size.x):
                sprite_name = ''
                if j == 0:
                    if i == 0:
                        sprite_name += 'wall_10'
                    elif i == size.x - 1:
                        sprite_name += 'wall_11'
                    else:
                        sprite_name += 'wall_8'
                elif j == size.y - 1:
                    if i == 0:
                        sprite_name += 'wall_12'
                    elif i == size.x - 1:
                        sprite_name += 'wall_13'
                    else:
                        sprite_name += 'wall_2'
                else:
                    if i == 0:
                        sprite_name += 'wall_6'
                    elif i == size.x - 1:
                        sprite_name += 'wall_4'
                    else:
                        sprite_name += 'empty'
                sprite_idx = self._resources.get_sprite_library()[sprite_name]['default_idx']
                self._get_drawer(i, j).draw(position.move(i, j) + self._offset, self._sprite, sprite_idx)


class MenuDrawer:

    _offset = Vector2(-8, -8)

    def __init__(self, services, canvas):
        self._services = services
        self._graphics = self._services[AbstractGraphics]
        self._canvas = canvas
        self._title_drawer = TextDrawer(self._services, self._canvas)
        self._content_drawers = []
        self._background_drawer = BackgroundDrawer(self._services, self._canvas)

    def initial_draw(self, model):
        world_size = model.get_size()
        screen_size = self._graphics.world_space_to_screen_space(world_size)
        self._canvas.set_size(screen_size)
        self._background_drawer.draw(Vector2.zero(), world_size)

    def _draw_content(self, model, content):
        while self._content_drawers:
            drawer = self._content_drawers.pop()
            drawer.clear()
        for i, line in enumerate(content):
            x = model.get_size().x / 2
            y = (model.get_size().y - len(content)) / 2 + i
            drawer = TextDrawer(self._services, self._canvas)
            self._content_drawers.append(drawer)
            drawer.draw(Vector2(x, y), line)

    def _draw_page(self, model, menu, prev_content):
        for i, (caption, _, _, _) in enumerate(menu.current_page.items):
            if i == menu.current_page.pointer:
                prev_content.append('> ' + caption + '  ')
            else:
                prev_content.append(caption)
        self._draw_content(model, prev_content)

    def _draw_ratings(self, model, menu, prev_content):
        for i, (name, rating) in enumerate(menu.current_page.ratings):
            space = '.' * (16 - (len(name) + len(str(rating))))
            prev_content.append(str(i + 1) + '.' + name + space + str(rating))
        prev_content.append('')
        self._draw_page(model, menu, prev_content)

    def _draw_record(self, model, menu, prev_content):
        first = ''
        second = ''
        third = ''
        for i, p in enumerate(menu.current_page.cache['name']):
            first += '^' if menu.current_page.char_pointer == i else ' '
            second += self._services[AbstractConfig]['gameplay']['symbols'][p]
            third += '`' if menu.current_page.char_pointer == i else ' '
        prev_content.append(first)
        prev_content.append(second)
        prev_content.append(third)
        prev_content.append('')
        self._draw_page(model, menu, prev_content)

    def draw(self, model):
        if not model:
            return
        x = model.get_size().x / 2
        y = model.get_size().y / 4
        self._title_drawer.draw(Vector2(x, y), model.menu.current_page.title)
        if model.menu.current_page is RatingsItem:
            self._draw_ratings(model, model.menu, [])
        elif model.menu.current_page is RecordItem:
            self._draw_record(model, model.menu, [])
        else:
            self._draw_page(model, model.menu, [])

    def clear(self):  # todo
        pass


class GameDrawer:

    def __init__(self, services, canvas):
        self._services = services
        self._config = self._services[AbstractConfig]
        self._graphics = self._services[AbstractGraphics]
        self._resources = self._services[ResourceManager]
        self._canvas = canvas
        self._actor_drawers = {}
        self._block_drawers = {}
        self._text_drawer = TextDrawer(self._services, self._canvas)
        self._actor_drawers['pacman'] = PacmanDrawer(
            self._graphics,
            self._canvas,
            self._resources
        )
        self._actor_drawers['red_ghost'] = EnemyDrawer(
            self._graphics,
            self._canvas,
            self._resources,
            'red_ghost',
            (1, 0, 0, 1)
        )
        self._actor_drawers['pink_ghost'] = EnemyDrawer(
            self._graphics,
            self._canvas,
            self._resources,
            'pink_ghost',
            (1, 0.6, 0.6, 1)
        )
        self._actor_drawers['blue_ghost'] = EnemyDrawer(
            self._graphics,
            self._canvas,
            self._resources,
            'blue_ghost',
            (0, 0.74, 1, 1)
        )
        self._actor_drawers['orange_ghost'] = EnemyDrawer(
            self._graphics,
            self._canvas,
            self._resources,
            'orange_ghost',
            (1, 0.54, 0, 1)
        )
        self._level_drawers = TextDrawer(services, self._canvas)
        self._scores_drawers = TextDrawer(services, self._canvas)
        self._lives_drawers = TextDrawer(services, self._canvas)
        self._background_drawer = None

    def initial_draw(self, model):
        self._canvas.set_size(model.get_size() * self._config['view']['px_per_unit'] * self._config['view']['scale'])
        for x in range(model.field.grid.size.x):
            for y in range(model.field.grid.size.y):
                self._block_drawers[Vector2(x, y)] = BlockDrawer(
                    self._services,
                    self._canvas
                )
        self._background_drawer = BackgroundDrawer(self._services, self._canvas)
        self._background_drawer.draw(model.field.grid.size.with_(y=0), model.get_size())

    def draw(self, model):
        if not model:
            return
        for block in model.field.grid:
            try:
                self._block_drawers[block.cell].draw(block, model.field)
            except KeyError:
                pass
        for actor in model.field.actors.values():
            self._actor_drawers[actor.name].draw(actor)
        self._level_drawers.draw(
            Vector2(model.field.grid.size.x + 1, 1),
            f'level: {model.level}',
            TextDrawer.Align.LEFT
        )
        self._scores_drawers.draw(
            Vector2(model.field.grid.size.x + 1, 3),
            f'scores: {model.scores}',
            TextDrawer.Align.LEFT
        )
        self._lives_drawers.draw(
            Vector2(model.field.grid.size.x + 1, 5),
            f'lives: {model.lives}',
            TextDrawer.Align.LEFT
        )


class CaptionDrawer:

    def __init__(self, services, canvas):
        self._services = services
        self._canvas = canvas
        self._background_drawer = BackgroundDrawer(self._services, self._canvas)
        self._text_drawer = TextDrawer(self._services, self._canvas)

    def initial_draw(self, model):
        pass

    def draw(self, model):
        text = ''
        if model.mode == GameDriver.Mode.WIN:
            text = 'you win!'
        elif model.mode == GameDriver.Mode.LOSE:
            text = 'you lose...'

        self._background_drawer.draw(Vector2.zero(), model.get_size())
        self._text_drawer.draw(model.get_size() / 2, text)


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
            GameDriver.Mode.WIN: CaptionDrawer(self._services, self._canvas),
            GameDriver.Mode.LOSE: CaptionDrawer(self._services, self._canvas)
        }
        self._services[EventDispatcher].subscribe(EventId.MODEL_UPDATE, self._on_model_update)
        self._services[EventDispatcher].subscribe(EventId.REDRAW, self._on_redraw)

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
            if new in self._drawers:
                self._drawers[new].initial_draw(self._model)
        if self._model.mode in self._drawers:
            self._drawers[self._model.mode].draw(self._model)
        # todo отрисовывать акторов, только когда они в пределах видимой
        # todo области иначе обрезать
