

class Sprite:

    def __init__(self, *images):
        self._images = images

    def __getitem__(self, idx):
        return self._images[idx]

    def __len__(self):
        return len(self._images)


class SpriteDrawer:

    def __init__(self, graphics, canvas):
        self._graphics = graphics
        self._canvas = canvas
        self._canvas_id = None

    def draw(self, position, sprite, idx):
        texture = sprite[idx]
        self.clear()
        screen_position = self._graphics.world_space_to_screen_space(position)
        self._canvas_id = self._canvas.draw_image(texture, screen_position)

    def clear(self):
        if self._canvas_id:
            self._canvas.clear(self._canvas_id)
