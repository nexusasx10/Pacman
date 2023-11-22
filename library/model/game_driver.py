import logging
from enum import Enum

import datetime

from library.controller import Control
from library.event import EventId
from library.model.actor import Pacman, RedGhost, PinkGhost, BlueGhost, \
    OrangeGhost, Enemy
from library.model.field import Field, Block
from library.geometry import Direction, Vector
from library.model.menu import Menu, PageItem, RatingsItem, RecordItem, SaveItem, \
    LoadItem
from library.time import Scheduler


class GameDriver:

    class Mode(Enum):
        PLAY = 0
        MENU = 1
        WIN = 2
        LOSE = 3
        WAIT = 4
        FREE = 5
        PAUSE = 6

    class Difficulty(Enum):
        EASY = 0
        NORMAL = 1
        HARD = 2

    def __init__(self, services):
        self._services = services
        self.menu = None
        self._init_menu()
        self._scheduler = Scheduler(self._services.event_dispatcher)
        self.mode = self.Mode.MENU
        self.time = None
        self.grid = None
        self.difficulty = None
        self.level = None
        self.scores = None
        self.lives = None
        self.field = None
        self._dots = None
        self._services.event_dispatcher.subscribe(EventId.TICK, self._on_tick, 2)
        self._services.event_dispatcher.subscribe(EventId.PICKUP, self._on_pickup)
        self._services.event_dispatcher.subscribe(EventId.CONTROL, self._on_control)
        self._services.event_dispatcher.subscribe(EventId.STOP, self._on_stop)
        self._services.event_dispatcher.subscribe(EventId.GAME_START, self._on_game_start)
        self._services.event_dispatcher.subscribe(EventId.GAME_END, self._on_game_end)
        self._services.event_dispatcher.subscribe(EventId.GAME_RESTART, self._on_game_restart)
        self._services.event_dispatcher.subscribe(EventId.NEXT_LEVEL, self._on_next_level)

    def _init_menu(self):
        menu = Menu()
        menu.root_item = PageItem('pacman')
        menu.play_item = PageItem('play')
        menu.ratings_item = RatingsItem(self._services, 'ratings')
        menu.exit_item = PageItem('do you really want to exit?')
        menu.select_grid_item = PageItem('select grid')
        menu.select_difficulty_item = PageItem('select difficulty')
        menu.pause_item = PageItem('pause')
        menu.save_item = SaveItem(self._services, 'save', self.save_game)
        menu.load_item = LoadItem(self._services, 'load', self.load_game)
        menu.save_offer_item = PageItem('do you want to save progress?')
        menu.save_offer_item2 = PageItem('do you want to save progress?')
        menu.record_item = RecordItem(self._services, 'enter your name')

        menu.root_item.add_item('play', menu.play_item, True)
        menu.root_item.add_item('ratings', menu.ratings_item, True)
        menu.root_item.add_item('exit', menu.exit_item, True)

        menu.play_item.add_item('new game', menu.select_grid_item, True)
        menu.play_item.add_item('load', menu.load_item, True)
        menu.play_item.add_item('cancel', None, True, menu.back)

        menu.ratings_item.add_item('cancel', None, True, menu.back)

        menu.exit_item.add_item('no', None, True, menu.back)
        menu.exit_item.add_item(
            'yes',
            None,
            False,
            lambda: self._services.event_dispatcher.fire(EventId.STOP, self)
        )

        for grid in self._services.resources.list_grids():
            menu.select_grid_item.add_item(
                grid,
                menu.select_difficulty_item,
                True,
                lambda g=grid: menu.select_grid_item.cache.update(grid=g)
            )
        menu.select_grid_item.add_item('cancel', None, True, menu.back)

        for difficulty in self.Difficulty:
            menu.select_difficulty_item.add_item(
                difficulty.name.lower(),
                None,
                False,
                lambda dif=difficulty: self.new_game(
                    dif, menu.select_grid_item.cache['grid']
                )
            )
        menu.select_difficulty_item.add_item('cancel', None, True, menu.back)

        def plan_start():
            self.mode = self.Mode.WAIT
            self._scheduler.schedule(250, EventId.GAME_START)
        # todo esc redefine
        menu.pause_item.add_item('continue', None, False, plan_start)
        menu.pause_item.add_item('save', menu.save_item, True)
        menu.pause_item.add_item('main menu', menu.save_offer_item, True)

        menu.save_item.add_item('cancel', None, True, menu.back)

        menu.load_item.add_item('cancel', None, True, menu.back)

        def save_and_reset():
            self.save_game('quick')
            self._reset()

        menu.save_offer_item.add_item(
            'yes', menu.root_item, False, save_and_reset
        )
        menu.save_offer_item.add_item('no', menu.root_item, False, self._reset)
        menu.save_offer_item.add_item('cancel', None, True, menu.back)

        def save_and_destroy():
            self.save_game('quick')
            self._services.event_dispatcher.fire(EventId.DESTROY, self)

        menu.save_offer_item2.add_item('yes', None, False, save_and_destroy)
        menu.save_offer_item2.add_item(
            'no',
            None,
            False,
            lambda: self._services.event_dispatcher.fire(EventId.DESTROY, self)
        )
        menu.save_offer_item2.add_item('cancel', menu.pause_item, False)

        menu.record_item.add_item(
            'ok',
            menu.root_item,
            False,
            lambda: self._services.resources.add_rating(
                ''.join(
                    map(
                        lambda i: self._services.config['model']['symbols'][i],
                        menu.record_item.cache['name']
                    )
                ),
                self.scores
            )
        )
        menu.record_item.add_item('cancel', menu.root_item, False)

        menu.current_page = menu.root_item
        self.menu = menu

    def _initiate(self, time, grid, difficulty, level, scores, lives):
        self.time = time
        self.grid = grid
        self.difficulty = difficulty
        self.level = level
        self.scores = scores
        self.lives = lives
        self.field = Field(
            self._services, self._services.resources.get_grid(grid)
        )
        self._dots = self._services.config['model']['dot_count']

    def _reset(self):
        self._scheduler.reset()
        if self.field:
            for actor in self.field.actors.values():
                actor.destroy()
        self.time = None
        self.grid = None
        self.difficulty = None
        self.level = None
        self.scores = None
        self.lives = None
        self.field = None
        self._dots = None

    def new_game(self, difficulty, grid):
        self._reset()
        lives = self._services.config['model']['start_lives']
        self._initiate(0, grid, difficulty, 1, 0, lives)
        self._services.event_dispatcher.fire(EventId.GAME_INIT, self)
        if difficulty == self.Difficulty.EASY:
            enemy_start_mode = Enemy.Mode.FREE
        elif difficulty == self.Difficulty.NORMAL:
            enemy_start_mode = Enemy.Mode.SCATTER
            self._scheduler.schedule(1000, EventId.SWITCH_TIMEOUT)
            self._services.event_dispatcher.subscribe(EventId.SWITCH_TIMEOUT, self._on_switch_timeout)
        else:
            enemy_start_mode = Enemy.Mode.CHASE
        self.field.spawn_actor(
            Pacman,
            self.field.grid.anchors['pacman'].shift(1, 0.5),
            Direction.WEST,
            (Pacman.Mode.NONE, Pacman.Mode.WALKING)
        )
        self.field.spawn_actor(
            RedGhost,
            self.field.grid.anchors['enemies'].shift(4, -0.5),
            Direction.WEST,
            (Enemy.Mode.NONE, enemy_start_mode, Enemy.Mode.NONE)
        )
        self.field.spawn_actor(
            PinkGhost,
            self.field.grid.anchors['enemies'].shift(4, 2.5),
            Direction.NORTH,
            (Enemy.Mode.NONE, enemy_start_mode, Enemy.Mode.HOME)
        )
        self.field.spawn_actor(
            BlueGhost,
            self.field.grid.anchors['enemies'].shift(2, 2.5),
            Direction.SOUTH,
            (Enemy.Mode.NONE, enemy_start_mode, Enemy.Mode.HOME)
        )
        self.field.spawn_actor(
            OrangeGhost,
            self.field.grid.anchors['enemies'].shift(6, 2.5),
            Direction.SOUTH,
            (Enemy.Mode.NONE, enemy_start_mode, Enemy.Mode.HOME)
        )
        self.mode = self.Mode.WAIT
        self._scheduler.schedule(250, EventId.GAME_START)
        self._scheduler.schedule(300, EventId.PINK_GHOST_OUT)
        self._scheduler.schedule(400, EventId.BLUE_GHOST_OUT)
        self._scheduler.schedule(500, EventId.ORANGE_GHOST_OUT)

    def load_game(self, save_index):
        save = self._services.resources.get_save(save_index)
        self._reset()
        time = save['game']['time']
        grid = save['game']['grid']
        difficulty = save['game']['difficulty']
        level = save['game']['level']
        scores = save['game']['scores']
        lives = save['game']['lives']
        self._initiate(time, grid, self.Difficulty[difficulty],
                       level, scores, lives)
        self._dots = save['game']['dots']
        self._scheduler.load(save['scheduler'])
        for cell in save['blocks']:
            cell_p = Vector(*map(int, cell.split(',')))
            self.field.grid[cell_p].content = Block.Content[
                save['blocks'][cell]
            ]
        self.field.spawn_actor(
            Pacman,
            Vector(*map(float, save['pacman']['position'].split(','))),
            Direction[save['pacman']['direction']],
            (
                Pacman.Mode[save['pacman']['mode1']],
                Pacman.Mode[save['pacman']['mode2']]
            )
        )
        if save['pacman']['last_turn'] != 'None':
            self.field.actors['pacman'].last_turn = Vector(
                *map(float, save['pacman']['last_turn'].split(','))
            )
        self.field.spawn_actor(
            RedGhost,
            Vector(*map(float, save['red_ghost']['position'].split(','))),
            Direction[save['red_ghost']['direction']],
            (
                Enemy.Mode[save['red_ghost']['mode1']],
                Enemy.Mode[save['red_ghost']['mode2']],
                Enemy.Mode[save['red_ghost']['mode3']],
            )
        )
        if save['red_ghost']['last_turn'] != 'None':
            self.field.actors['red_ghost'].last_turn = Vector(
                *map(float, save['red_ghost']['last_turn'].split(','))
            )
        if save['red_ghost']['last_node'] != 'None':
            self.field.actors['red_ghost'].last_node = save['red_ghost'][
                'last_node'
            ]
        self.field.spawn_actor(
            PinkGhost,
            Vector(*map(float, save['pink_ghost']['position'].split(','))),
            Direction[save['pink_ghost']['direction']],
            (
                Enemy.Mode[save['pink_ghost']['mode1']],
                Enemy.Mode[save['pink_ghost']['mode2']],
                Enemy.Mode[save['pink_ghost']['mode3']],
            )
        )
        if save['pink_ghost']['last_turn'] != 'None':
            self.field.actors['pink_ghost'].last_turn = Vector(
                *map(float, save['pink_ghost']['last_turn'].split(','))
            )
        if save['pink_ghost']['last_node'] != 'None':
            self.field.actors['pink_ghost'].last_node = save['pink_ghost'][
                'last_node'
            ]
        self.field.spawn_actor(
            BlueGhost,
            Vector(*map(float, save['blue_ghost']['position'].split(','))),
            Direction[save['blue_ghost']['direction']],
            (
                Enemy.Mode[save['blue_ghost']['mode1']],
                Enemy.Mode[save['blue_ghost']['mode2']],
                Enemy.Mode[save['blue_ghost']['mode3']],
            )
        )
        if save['blue_ghost']['last_turn'] != 'None':
            self.field.actors['blue_ghost'].last_turn = Vector(
                *map(float, save['blue_ghost']['last_turn'].split(','))
            )
        if save['blue_ghost']['last_node'] != 'None':
            self.field.actors['blue_ghost'].last_node = save['blue_ghost'][
                'last_node'
            ]
        self.field.spawn_actor(
            OrangeGhost,
            Vector(*map(float, save['orange_ghost']['position'].split(','))),
            Direction[save['orange_ghost']['direction']],
            (
                Enemy.Mode[save['orange_ghost']['mode1']],
                Enemy.Mode[save['orange_ghost']['mode2']],
                Enemy.Mode[save['orange_ghost']['mode3']],
            )
        )
        if save['orange_ghost']['last_turn'] != 'None':
            self.field.actors['orange_ghost'].last_turn = Vector(
                *map(float, save['orange_ghost']['last_turn'].split(','))
            )
        if save['orange_ghost']['last_node'] != 'None':
            self.field.actors['orange_ghost'].last_node = save['orange_ghost'][
                'last_node'
            ]
        self.mode = self.Mode.WAIT
        self._scheduler.schedule(250, EventId.GAME_START)

    def save_game(self, save_index):
        if self.mode not in (self.Mode.PLAY, self.Mode.MENU):
            return
        mode = self.mode
        self.mode = self.Mode.PAUSE
        save = {
            'info': {
                'date': datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            },
            'game': {
                'time': self.time,
                'grid': self.grid,
                'difficulty': self.difficulty.name,
                'level': self.level,
                'scores': self.scores,
                'lives': self.lives,
                'dots': self._dots
            },
            'scheduler': self._scheduler.store(),
            'blocks': {
                block.cell: block.content.name for block in self.field.grid
            },
            'pacman': {
                'position': self.field.actors['pacman'].position,
                'direction': self.field.actors['pacman'].direction.name,
                'mode1': self.field.actors['pacman'].mode[0].name,
                'mode2': self.field.actors['pacman'].mode[1].name,
                'last_turn': str(self.field.actors['pacman'].last_turn),
            },
            'red_ghost': {
                'position': self.field.actors['red_ghost'].position,
                'direction': self.field.actors['red_ghost'].direction.name,
                'mode1': self.field.actors['red_ghost'].mode[0].name,
                'mode2': self.field.actors['red_ghost'].mode[1].name,
                'mode3': self.field.actors['red_ghost'].mode[2].name,
                'last_turn': str(self.field.actors['red_ghost'].last_turn),
                'last_node': str(self.field.actors['red_ghost'].last_node),
            },
            'pink_ghost': {
                'position': self.field.actors['pink_ghost'].position,
                'direction': self.field.actors['pink_ghost'].direction.name,
                'mode1': self.field.actors['pink_ghost'].mode[0].name,
                'mode2': self.field.actors['pink_ghost'].mode[1].name,
                'mode3': self.field.actors['pink_ghost'].mode[2].name,
                'last_turn': str(self.field.actors['pink_ghost'].last_turn),
                'last_node': str(self.field.actors['pink_ghost'].last_node),
            },
            'blue_ghost': {
                'position': self.field.actors['blue_ghost'].position,
                'direction': self.field.actors['blue_ghost'].direction.name,
                'mode1': self.field.actors['blue_ghost'].mode[0].name,
                'mode2': self.field.actors['blue_ghost'].mode[1].name,
                'mode3': self.field.actors['blue_ghost'].mode[2].name,
                'last_turn': str(self.field.actors['blue_ghost'].last_turn),
                'last_node': str(self.field.actors['blue_ghost'].last_node),
            },
            'orange_ghost': {
                'position': self.field.actors['orange_ghost'].position,
                'direction': self.field.actors['orange_ghost'].direction.name,
                'mode1': self.field.actors['orange_ghost'].mode[0].name,
                'mode2': self.field.actors['orange_ghost'].mode[1].name,
                'mode3': self.field.actors['orange_ghost'].mode[2].name,
                'last_turn': str(self.field.actors['orange_ghost'].last_turn),
                'last_node': str(self.field.actors['orange_ghost'].last_node),
            }
        }
        self._services.resources.add_save(save_index, save)
        self.mode = mode

    def _on_next_level(self, event_args):
        for actor in self.field.actors.values():
            actor.destroy()
        self.field = Field(
            self._services, self._services.resources.get_grid(self.grid)
        )
        self._dots = self._services.config['model']['dot_count']  # todo
        self._services.event_dispatcher.fire(EventId.GAME_RESTART, self)

    def _on_game_restart(self, event_args):
        self._scheduler.reset()
        if self.difficulty == self.Difficulty.EASY:
            enemy_start_mode = Enemy.Mode.FREE
        elif self.difficulty == self.Difficulty.NORMAL:
            enemy_start_mode = Enemy.Mode.SCATTER
            self._scheduler.schedule(1000, EventId.SWITCH_TIMEOUT)
            self._services.event_dispatcher.subscribe(EventId.SWITCH_TIMEOUT, self._on_switch_timeout)
        else:
            enemy_start_mode = Enemy.Mode.CHASE
        self.field.spawn_actor(
            Pacman,
            self.field.grid.anchors['pacman'].shift(1, 0.5),
            Direction.WEST,
            (Pacman.Mode.NONE, Pacman.Mode.WALKING)
        )
        self.field.spawn_actor(
            RedGhost,
            self.field.grid.anchors['enemies'].shift(4, -0.5),
            Direction.WEST,
            (Enemy.Mode.NONE, enemy_start_mode, Enemy.Mode.NONE)
        )
        self.field.spawn_actor(
            PinkGhost,
            self.field.grid.anchors['enemies'].shift(4, 2.5),
            Direction.NORTH,
            (Enemy.Mode.NONE, enemy_start_mode, Enemy.Mode.HOME)
        )
        self.field.spawn_actor(
            BlueGhost,
            self.field.grid.anchors['enemies'].shift(2, 2.5),
            Direction.SOUTH,
            (Enemy.Mode.NONE, enemy_start_mode, Enemy.Mode.HOME)
        )
        self.field.spawn_actor(
            OrangeGhost,
            self.field.grid.anchors['enemies'].shift(6, 2.5),
            Direction.SOUTH,
            (Enemy.Mode.NONE, enemy_start_mode, Enemy.Mode.HOME)
        )
        self.mode = self.Mode.WAIT
        self._scheduler.schedule(250, EventId.GAME_START)
        self._scheduler.schedule(300, EventId.PINK_GHOST_OUT)
        self._scheduler.schedule(400, EventId.BLUE_GHOST_OUT)
        self._scheduler.schedule(500, EventId.ORANGE_GHOST_OUT)

    def _on_game_start(self, event_id):
        self.mode = self.Mode.PLAY

    def _on_game_end(self, event_args):
        self.mode = self.Mode.LOSE

    def _on_tick(self, event_args):
        if self.mode == self.Mode.PLAY:
            self.time += 1
            if self._dots == 0:
                self.mode = self.Mode.FREE
                self.level += 1
                if self.level > self._services.config['model']['max_level']:
                    self.mode = self.Mode.WIN
                else:
                    self._services.event_dispatcher.fire(EventId.NEXT_LEVEL, self)
            elif self.field.actors['pacman'].mode[0] == Pacman.Mode.DEAD:
                self.mode = self.Mode.FREE
                self.lives -= 1
                if self.lives:
                    self._scheduler.schedule(300, EventId.GAME_RESTART)
                else:
                    self._scheduler.schedule(300, EventId.GAME_END)
            self.field.update()
        elif self.mode == self.Mode.FREE:
            self.field.update()
        self._services.event_dispatcher.fire(EventId.MODEL_UPDATE, self, model=self)

    def _on_control(self, event_args):
        if self.mode == self.Mode.MENU:
            if event_args.value == Control.DOWN:
                self.menu.down()
            elif event_args.value == Control.UP:
                self.menu.up()
            elif event_args.value == Control.RIGHT:
                self.menu.right()
            elif event_args.value == Control.LEFT:
                self.menu.left()
            elif event_args.value == Control.ENTER:
                self.menu.enter()
            elif event_args.value == Control.EXIT:
                self.menu.back()
        elif self.mode == self.Mode.PLAY:
            if event_args.value == Control.EXIT:
                self.menu.current_page = self.menu.pause_item
                self.menu.current_page.reset()
                self.mode = self.Mode.MENU
            if event_args.value == Control.SAVE:
                self.save_game('quick')
        elif self.mode in (self.Mode.WIN, self.Mode.LOSE):
            self.menu.current_page = self.menu.record_item
            self.mode = self.Mode.MENU

    def _on_stop(self, event_args):
        if self.mode == self.Mode.PLAY:
            self.menu.current_page = self.menu.save_offer_item2
            self.menu.current_page.reset()
            self.mode = self.Mode.MENU
        else:
            self._services.event_dispatcher.fire(EventId.DESTROY, self)

    def _on_switch_timeout(self, event_args):
        self._scheduler.schedule(1000, EventId.SWITCH_TIMEOUT)

    def _on_pickup(self, event_args):
        if event_args.pickup == Block.Content.ENERGIZER:
            self.scores += 100
            self._scheduler.schedule(600, EventId.FRIGHTENED_TIMEOUT)
            self._scheduler.schedule(800, EventId.ENERGIZER_TIMEOUT)
        elif event_args.pickup == Block.Content.DOT:
            self.scores += 10
            self._dots -= 1
        elif event_args.pickup == Block.Content.FRUIT:
            self.scores += 500
