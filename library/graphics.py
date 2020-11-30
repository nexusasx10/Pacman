import copy

from library.model.field import Block


class Animation:

    def __init__(self, services, name, sequence, cycled):
        self._services = services
        self._name = name
        self._sequence = sequence
        self._cycled = cycled
        self._pointer = 0

    def have_frame(self):
        return self._cycled or self._pointer < len(self._sequence)

    def get(self):
        pointer = self._pointer
        self._pointer += 1
        if self._pointer >= len(self._sequence):
            if self._cycled:
                self._pointer -= len(self._sequence)
            else:
                self._pointer -= 1
        return self._services.resources.get_texture(
            self._name, self._sequence[pointer]
        )


class AnimationDrawer:

    def __init__(self, services, display):
        self._services = services
        self._display = display
        self._display_id = None
        self._current_animation = None
        self._current_animation_name = None

    def draw(self, position, offset, name, animation_name):
        if self._current_animation_name != (name, animation_name):
            self._current_animation_name = name, animation_name
            animation = self._services.resources.get_animation(
                name, animation_name
            )
            self._current_animation = copy.copy(animation)
        texture = self._current_animation.get()
        self.clear()
        self._display_id = self._display.create_image(
            position.x * Block.size.width + offset.x,
            position.y * Block.size.height + offset.y,
            image=texture,
            anchor='nw'
        )

    def clear(self):
        if self._display_id:
            self._display.delete(self._display_id)
