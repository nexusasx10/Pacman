

class Sprite:

    def __init__(self, *images):
        self._images = images

    def __getitem__(self, idx):
        return self._images[idx]


class Animation:

    def __init__(self, sequence, params):
        self._sequence = sequence
        self._params = params
        self._pointer = 0

    def set_param(self, name, value):
        self._params['direction'] = value

    def _is_looped(self):
        return 'is_looped' in self._params

    def _get_param(self, type_, name):
        param = self._params[name]
        return type_(param)

    def _get_offset(self):
        param_names = {
            'direction': 'direction_offset',
            'type': 'type_offset'
        }
        offset = 0
        for trigger_param_name in param_names:
            if trigger_param_name in self._params:
                application_param_name = self._params[trigger_param_name]
                if application_param_name in self._params:
                    offset += self._get_param(int, trigger_param_name) * self._get_param(int, application_param_name)
        return offset

    def get_next_frame(self, sprite):
        pointer = self._pointer
        self._pointer += 1
        if self._pointer >= len(self._sequence):
            if self._is_looped():
                self._pointer = 0
            else:
                self._pointer -= 1
        idx = self._sequence[pointer] + self._get_offset()
        return sprite[idx]

    def reset(self):
        self._pointer = 0


class AnimationDrawer:

    def __init__(self, graphics, canvas):
        self._graphics = graphics
        self._canvas = canvas
        self._canvas_id = None
        self._current_animation = None
        self._current_animation_name = None

    def draw(self, position, sprite, animation):
        texture = animation.get_next_frame(sprite)
        self.clear()
        screen_position = self._graphics.world_space_to_screen_space(position)
        self._canvas_id = self._canvas.draw_image(texture, screen_position)

    def clear(self):
        if self._canvas_id:
            self._canvas.clear(self._canvas_id)
