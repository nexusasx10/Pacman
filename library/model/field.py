import itertools
from enum import Enum

from library.event import EventArgs, EventId
from library.geometry import Size, Direction


class Block:

    size = Size(16, 16)

    class Content(Enum):
        EMPTY = 0
        DOT = 1
        ENERGIZER = 2
        FRUIT = 3
        DOOR = 4
        WALL = 5

    def __init__(self, cell, content, connections):
        self.cell = cell
        self.content = content
        self.connections = connections


class Grid:

    size = Size(28, 31)

    def __init__(self, anchors):
        width, height = self.size.width, self.size.height
        self.dimensions = [[None for c in range(width)] for r in range(height)]
        self.anchors = anchors

    def __getitem__(self, cell):
        x = cell.x % self.size.width
        y = cell.y % self.size.height
        return self.dimensions[y][x]

    def __setitem__(self, cell, value):
        self.dimensions[cell.y][cell.x] = value

    def __iter__(self):
        return itertools.chain(*self.dimensions)


class Graph:

    def __init__(self):
        self.nodes = {}
        self.exit = {}

    def add_node(self, position):
        self.nodes[len(self.nodes)] = position


class Field:

    def __init__(self, services, grid):
        self._services = services
        self.actors = {}
        self.grid = grid
        self.enemy_graph = Graph()
        self._build_graph()

    def _build_graph(self):
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(2, 2))
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(2, 2.5))
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(2, 3))
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(4, 2))
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(4, 2.5))
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(4, 3))
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(6, 2))
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(6, 2.5))
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(6, 3))
        self.enemy_graph.add_node(self.grid.anchors['enemies'].shift(4, -0.5))

        self.enemy_graph.exit[0] = Direction.SOUTH
        self.enemy_graph.exit[1] = Direction.EAST
        self.enemy_graph.exit[2] = Direction.NORTH
        self.enemy_graph.exit[3] = Direction.NORTH
        self.enemy_graph.exit[4] = Direction.NORTH
        self.enemy_graph.exit[5] = Direction.NORTH
        self.enemy_graph.exit[6] = Direction.SOUTH
        self.enemy_graph.exit[7] = Direction.WEST
        self.enemy_graph.exit[8] = Direction.NORTH
        self.enemy_graph.exit[9] = Direction.WEST

    def update(self):
        for actor in self.actors.values():
            actor.update()
        self._notify_crossways()
        self._notify_pickups()
        self._notify_intersections()
        self._notify_ghost_events()

    def spawn_actor(self, actor_cls, position, direction, mode):
        actor = actor_cls(self._services, position, direction, mode, self)
        self.actors[actor.name] = actor

    def _notify_intersections(self):
        pacman = self.actors['pacman']
        for enemy in self.actors.values():
            if enemy == pacman:
                continue
            if pacman.cell == enemy.cell:
                self._services.event_dispatcher.fire(EventId.INTERSECTION, self, enemy=enemy)

    def _notify_crossways(self):
        for actor in self.actors.values():
            neighbors = set(self.grid[actor.cell].connections.values())
            if neighbors not in (
                    {Direction.NORTH, Direction.SOUTH},
                    {Direction.EAST, Direction.WEST}
            ):
                # todo повысить погрешность и выравнивать положение
                if actor.position.distance(actor.cell.shift(0.5, 0.5)) < 0.15:
                    self._services.event_dispatcher.fire(EventId.CROSSWAY, self, actor=actor)

    def _notify_pickups(self):
        pacman = self.actors['pacman']
        if self.grid[pacman.cell].content != Block.Content.EMPTY:
            self._services.event_dispatcher.fire(EventId.PICKUP, self, pickup=self.grid[pacman.cell].content)
            self.grid[pacman.cell].content = Block.Content.EMPTY

    def _notify_ghost_events(self):
        for actor in self.actors.values():
            if actor.name == 'pacman':
                continue
            if actor.position.distance(actor.dead_target) < 0.15:
                self._services.event_dispatcher.fire(EventId.GHOST_ON_DEAD_TARGET, self, name=actor.name)
            if actor.position.distance(
                    self.grid.anchors['enemies'].shift(4, -0.5)
            ) < 0.15:
                self._services.event_dispatcher.fire(EventId.GHOST_BEHIND_DOOR, self, name=actor.name)
