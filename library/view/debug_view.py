from library.event import EventId
from library.model.actor import Enemy
from library.model.field import Block
from library.model.game_driver import GameDriver


class EnemyDrawer:

    def __init__(self, services, display, color):
        self._services = services
        self._display = display
        self._display_id = None
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
        self._display_id = self._display.create_line(
            actor.position.x * Block.size.x,
            actor.position.y * Block.size.y,
            actor.get_target().x * Block.size.x,
            actor.get_target().y * Block.size.y,
            fill=self._color
        )

    def clear(self):
        self._display.delete(self._display_id)


class DebugView:

    def __init__(self, services, root):
        self._services = services
        self._root = root
        self._model = None
        self._actor_drawers = {
            'red_ghost': EnemyDrawer(
                self._services,
                self._root.display,
                '#f00'
            ),
            'pink_ghost': EnemyDrawer(
                self._services,
                self._root.display,
                '#f99'
            ),
            'blue_ghost': EnemyDrawer(
                self._services,
                self._root.display,
                '#0cf'
            ),
            'orange_ghost': EnemyDrawer(
                self._services,
                self._root.display,
                '#f90'
            )
        }
        self._services.event_dispatcher.subscribe(EventId.MODEL_UPDATE, self._on_model_update)
        self._services.event_dispatcher.subscribe(EventId.REDRAW, self._on_redraw)

    def _on_model_update(self, event_args):
        self._model = event_args.model

    def _on_redraw(self, event_args):
        if not self._model:
            return
        if self._model.mode == GameDriver.Mode.PLAY:
            for actor in self._model.field.actors.values():
                if actor.name in self._actor_drawers:
                    self._actor_drawers[actor.name].draw(actor)
