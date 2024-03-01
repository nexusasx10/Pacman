from library.event import EventId, EventDispatcher
from library.model.actor import Enemy
from library.model.field import Block
from library.model.game_driver import GameDriver


class EnemyDrawer:

    def __init__(self, services, canvas, color):
        self._services = services
        self._canvas = canvas
        self._canvas_id = None
        self._color = color

    def draw(self, actor):
        self.clear()
        if (
                actor.mode[1] == Enemy.Mode.FREE or
                actor.mode[0] in (
                    Enemy.Mode.FRIGHTENED,
                    Enemy.Mode.FRIGHTENED_END
                )
        ):
            return
        self._canvas_id = self._canvas.draw_line(
            actor.position.scale(Block.size),
            actor.get_target().scale(Block.size),
            self._color
        )

    def clear(self):
        self._canvas.clear(self._canvas_id)


class DebugView:

    def __init__(self, services, canvas):
        self._services = services
        self._event_dispatcher = self._services[EventDispatcher]
        self._canvas = canvas
        self._model = None
        self._actor_drawers = {
            'red_ghost': EnemyDrawer(
                self._services,
                self._canvas,
                '#f00'
            ),
            'pink_ghost': EnemyDrawer(
                self._services,
                self._canvas,
                '#f99'
            ),
            'blue_ghost': EnemyDrawer(
                self._services,
                self._canvas,
                '#0cf'
            ),
            'orange_ghost': EnemyDrawer(
                self._services,
                self._canvas,
                '#f90'
            )
        }
        self._event_dispatcher.subscribe(EventId.MODEL_UPDATE, self._on_model_update)
        self._event_dispatcher.subscribe(EventId.REDRAW, self._on_redraw)

    def _on_model_update(self, event_args):
        self._model = event_args.model

    def _on_redraw(self, event_args):
        if not self._model:
            return
        if self._model.mode == GameDriver.Mode.PLAY:
            for actor in self._model.field.actors.values():
                if actor.name in self._actor_drawers:
                    self._actor_drawers[actor.name].draw(actor)
