import math
import random
import weakref
from abc import ABC, abstractmethod
from enum import Enum

from library.config import AbstractConfig
from library.model.control import InputUid
from library.events import EventId, EventDispatcher
from library.geometry import Vector2, Direction
from library.model.field import Block
from library.model.state_driver import StateDriver


class Actor(ABC):

    speeds = None
    size = Vector2(2, 2)

    def __init__(self, services, name, position, direction, field):
        self._services = services
        self._event_dispatcher = self._services[EventDispatcher]
        self.name = name
        self.position = position
        self.direction = direction
        self.max_speed = 0.1  # todo outer, переделать проверки перекрёстков
        self._weak_field = weakref.ref(field)
        self._event_dispatcher.subscribe(EventId.CROSSWAY, self._on_crossway)
        self.sprite_idx = 0

    def destroy(self):
        self._event_dispatcher.unsubscribe(EventId.CROSSWAY, self._on_crossway)

    @property
    @abstractmethod
    def mode(self):
        pass

    @property
    @abstractmethod
    def speed(self):
        pass

    @property
    def _field(self):
        return self._weak_field()

    @property
    def cell(self):
        return Vector2(
            math.floor(self.position.x),
            math.floor(self.position.y)
        )

    @abstractmethod
    def _on_crossway(self, event_args):
        pass

    def correct_position(self):
        self.position.x %= self._weak_field().grid.size.x
        self.position.y %= self._weak_field().grid.size.y

    def update(self):
        if self.position.distance(self.cell.move(0.5, 0.5)) < 0.06:
            if not self._field.grid[self.cell].connections[self.direction]:
                return
        dx, dy = map(lambda n: self.speed * n, self.direction.to_vector())
        self.position = self.position.move(dx, dy)
        self.correct_position()


class Pacman(Actor):

    class Mode(Enum):
        NONE = 0
        DEAD = 1
        ENERGIZER = 2
        WALKING = 3
        WAITING = 4

    speeds = {
        (Mode.NONE, Mode.WALKING): 0.8,
        (Mode.NONE, Mode.WAITING): 0,
        (Mode.DEAD, Mode.WALKING): 0,
        (Mode.DEAD, Mode.WAITING): 0,
        (Mode.ENERGIZER, Mode.WALKING): 0.9,
        (Mode.ENERGIZER, Mode.WAITING): 0
    }

    controls = {
        InputUid.RIGHT: Direction.EAST,
        InputUid.UP: Direction.NORTH,
        InputUid.LEFT: Direction.WEST,
        InputUid.DOWN: Direction.SOUTH
    }

    def __init__(self, services, position, direction, mode, field):
        super().__init__(services, 'pacman', position, direction, field)

        self.state_driver_1 = StateDriver(self._event_dispatcher, mode[0], self.name)
        self.state_driver_1.add_transition(
            EventId.INTERSECTION,
            (self.Mode.NONE,),
            self.Mode.DEAD,
            lambda args: not services[AbstractConfig]['debug']['is_god_mode']
        )
        self.state_driver_1.add_transition(
            EventId.PICKUP,
            (self.Mode.NONE,),
            self.Mode.ENERGIZER,
            lambda a: a.pickup == Block.Content.ENERGIZER
        )
        self.state_driver_1.add_transition(
            EventId.ENERGIZER_TIMEOUT,  # todo
            (self.Mode.ENERGIZER,),
            self.Mode.NONE
        )
        self.state_driver_2 = StateDriver(self._event_dispatcher, mode[1], self.name)
        self.state_driver_2.add_transition(
            EventId.CROSSWAY,
            (self.Mode.WALKING,),
            self.Mode.WAITING,
            lambda a: (
                a.actor.name == 'pacman'
                and not self._field.grid[self.cell].connections[self.direction]
            )
        )
        self.state_driver_2.add_transition(
            EventId.CONTROL,  # todo
            (self.Mode.WAITING,),
            self.Mode.WALKING,
            lambda a: (
                a.value in self.controls
                and self._field.grid[self.cell].connections[
                    self.controls[a.value]
                ]
            )
        )
        self.next_direction = None
        self.last_turn = None
        self._event_dispatcher.subscribe(EventId.CONTROL, self._on_control)  # todo

    def destroy(self):
        super().destroy()
        self._event_dispatcher.unsubscribe(EventId.CONTROL, self._on_control)
        self.state_driver_1.reset()
        self.state_driver_2.reset()

    @property
    def mode(self):
        return (
            self.state_driver_1.current_state,
            self.state_driver_2.current_state
        )

    @property
    def speed(self):
        return self.max_speed * self.speeds[self.mode]  # todo max_speed

    def _on_control(self, event_args):
        if event_args.value in self.controls:
            self.next_direction = self.controls[event_args.value]
            if self.direction.is_oppositely(self.next_direction):
                self.turn()

    def _on_crossway(self, event_args):
        if event_args.actor == self:
            self.turn()
            if self.last_turn != self.cell:
                self.position = self.cell.move(0.5, 0.5)
                self.last_turn = self.cell

    def turn(self):
        if not self.next_direction:
            return
        if self._field.grid[self.cell].connections[self.next_direction]:
            self.direction = self.next_direction
            self.next_direction = None


class Enemy(Actor):

    class Mode(Enum):
        NONE = 0
        DEAD = 1
        FRIGHTENED = 2
        FRIGHTENED_END = 3
        SCATTER = 4
        CHASE = 5
        FREE = 6
        HOME = 7
        EXIT = 8

    speeds = {
        Mode.NONE: 0.75,
        Mode.DEAD: 1,
        Mode.FRIGHTENED: 0.75,
        Mode.FRIGHTENED_END: 0.75
    }

    def __init__(self, services, name, position, direction, mode, field):
        super().__init__(services, name, position, direction, field)

        self.state_driver_1 = StateDriver(self._event_dispatcher, mode[0], self.name)
        self.state_driver_1.add_transition(
            EventId.INTERSECTION,
            (self.Mode.FRIGHTENED, self.Mode.FRIGHTENED_END),
            self.Mode.DEAD,
            lambda a: a.enemy == self
        )
        self.state_driver_1.add_transition(
            EventId.PICKUP,
            (self.Mode.NONE, self.Mode.FRIGHTENED_END),
            self.Mode.FRIGHTENED,
            lambda a: a.pickup == Block.Content.ENERGIZER
        )
        self.state_driver_1.add_transition(
            EventId.FRIGHTENED_TIMEOUT,
            (self.Mode.FRIGHTENED,),
            self.Mode.FRIGHTENED_END
        )
        self.state_driver_1.add_transition(
            EventId.ENERGIZER_TIMEOUT,
            (self.Mode.FRIGHTENED_END,),
            self.Mode.NONE
        )
        self.state_driver_1.add_transition(
            EventId.GHOST_BEHIND_DOOR,
            (self.Mode.DEAD,),
            self.Mode.NONE,
            lambda a: a.name == self.name
        )
        self.state_driver_2 = StateDriver(self._event_dispatcher, mode[1], self.name)
        self.state_driver_2.add_transition(
            EventId.SWITCH_TIMEOUT,
            (self.Mode.CHASE,),
            self.Mode.SCATTER
        )
        self.state_driver_2.add_transition(
            EventId.SWITCH_TIMEOUT,
            (self.Mode.SCATTER,),
            self.Mode.CHASE
        )
        self.state_driver_3 = StateDriver(self._event_dispatcher, mode[2], self.name)
        self.state_driver_3.add_transition(
            EventId.GHOST_BEHIND_DOOR,
            (self.Mode.EXIT,),
            self.Mode.NONE,
            lambda a: a.name == self.name
        )
        self.last_turn = None
        self.last_node = None
        self._event_dispatcher.subscribe(EventId.GHOST_BEHIND_DOOR, self._on_ghost_behind_door, -1)

    def destroy(self):
        super().destroy()
        self._event_dispatcher.unsubscribe(EventId.GHOST_BEHIND_DOOR, self._on_ghost_behind_door, -1)
        self.state_driver_1.reset()
        self.state_driver_2.reset()
        self.state_driver_3.reset()

    scatter_target = None

    @property
    @abstractmethod
    def chase_target(self):
        pass

    @property
    def dead_target(self):
        return self._field.grid.anchors['enemies'].move(4, -0.5)

    @property
    def mode(self):
        return (
            self.state_driver_1.current_state,
            self.state_driver_2.current_state,
            self.state_driver_3.current_state
        )

    @property
    def speed(self):
        return self.max_speed * self.speeds[self.mode[0]]

    def update(self):
        if self.mode[2] == self.Mode.HOME:
            current_node = self.current_node
            if current_node in (0, 3, 6) and current_node != self.last_node:
                self.direction = Direction.SOUTH
                self.last_node = current_node
            elif current_node in (2, 5, 8) and current_node != self.last_node:
                self.direction = Direction.NORTH
                self.last_node = current_node
        elif self.mode[2] == self.Mode.EXIT:
            current_node = self.current_node
            if current_node is not None and current_node != self.last_node:
                self.direction = self._field.enemy_graph.exit[current_node]
                new_position = self._field.enemy_graph.nodes[current_node]
                self.position = Vector2(new_position.x, new_position.y)
                self.last_node = current_node
        super().update()

    @property
    def current_node(self):
        for node in self._field.enemy_graph.nodes.items():
            if node[1].distance(self.position) < 0.15:
                return node[0]

    def get_target(self):
        if self.mode[0] == self.Mode.NONE:
            if self.mode[1] == self.Mode.SCATTER:
                return self.scatter_target
            elif self.mode[1] == self.Mode.CHASE:
                return self.chase_target
            else:
                return Vector2(
                    random.randint(0, self._weak_field().grid.size.x),
                    random.randint(0, self._weak_field().grid.size.y)
                )
        elif self.mode[0] == self.Mode.DEAD:
            return self.dead_target
        else:
            return Vector2(
                random.randint(0, self._weak_field().grid.size.x),
                random.randint(0, self._weak_field().grid.size.y)
            )

    def _on_crossway(self, event_args):
        if event_args.actor == self:
            if self.mode[2] not in (self.Mode.NONE, self.Mode.DEAD):
                return
            if self.last_turn and self.last_turn.distance(self.cell) < 1:
                return
            self.last_turn = self.cell
            current_block = self._field.grid[self.cell]
            self.direction = sorted(
                filter(
                    lambda d: (
                        current_block.connections[d]
                        and not self.direction.is_oppositely(d)
                    ),
                    current_block.connections
                ),
                key=lambda d: self._field.grid[
                    self.cell.move(*d.to_vector())
                ].cell.distance(self.get_target())
            )[0]

    def _on_ghost_behind_door(self, event_args):
        if self.name == event_args.name and self.mode[2] == self.Mode.EXIT:
            self.direction = Direction.WEST


class RedGhost(Enemy):

    def __init__(self, services, position, direction, mode, field):
        super().__init__(
            services, 'red_ghost', position, direction, mode, field
        )

    scatter_target = Vector2(26, 0)

    @property
    def chase_target(self):
        return self._field.actors['pacman'].position


class PinkGhost(Enemy):

    def __init__(self, services, position, direction, mode, field):
        super().__init__(
            services, 'pink_ghost', position, direction, mode, field
        )
        self.state_driver_3.add_transition(
            EventId.PINK_GHOST_OUT,
            (self.Mode.HOME,),
            self.Mode.EXIT
        )

    scatter_target = Vector2(1, 0)

    @property
    def chase_target(self):
        return self._field.actors['pacman'].position.move(
            *map(
                lambda n: 4 * n,
                self._field.actors['pacman'].direction.to_vector()
            )
        )


class BlueGhost(Enemy):

    def __init__(self, services, position, direction, mode, field):
        super().__init__(
            services, 'blue_ghost', position, direction, mode, field
        )
        self.state_driver_3.add_transition(
            EventId.BLUE_GHOST_OUT,
            (self.Mode.HOME,),
            self.Mode.EXIT
        )

    scatter_target = Vector2(26, 30)

    @property
    def chase_target(self):
        target = self._field.actors['pacman'].position.move(
            *map(
                lambda n: 2 * n,
                self._field.actors['pacman'].direction.to_vector()
            )
        )
        assistant = -self._field.actors['red_ghost'].position + target * 2
        return assistant


class OrangeGhost(Enemy):

    def __init__(self, services, position, direction, mode, field):
        super().__init__(
            services, 'orange_ghost', position, direction, mode, field
        )
        self.state_driver_3.add_transition(
            EventId.ORANGE_GHOST_OUT,
            (self.Mode.HOME,),
            self.Mode.EXIT
        )

    scatter_target = Vector2(1, 30)

    @property
    def chase_target(self):
        if self._field.actors['pacman'].position.distance(self.position) > 8:
            return self._field.actors['pacman'].position
        else:
            return self.scatter_target
