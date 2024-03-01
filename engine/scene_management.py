from engine.actor import Actor
from engine.transform import Transform2d


class Scene:

    def __init__(self):
        self.actors = []

    def add_actor(self, name='Actor', add_transform=False, parent=None):
        actor = Actor(name)

        if add_transform:
            transform = actor.add_component(Transform2d)
            if parent is None:
                self.actors.append(actor)
            else:
                transform.parent = parent
        elif parent is not None:
            raise ValueError('Can\'t attach static actor to transform.')
        else:
            self.actors.append(actor)

        return actor


class SceneManager:

    def __init__(self):
        self._current_scene = None

    def current_scene(self):
        return self._current_scene

    def load_scene(self, scene):
        self._current_scene = scene
