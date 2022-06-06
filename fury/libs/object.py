import numpy as np


class Object:
    def __init__(self, size=np.array([32, 32]), pos=np.array([0, 0]), color=np.array([255, 255, 255]),
                 scale=np.array([1, 1]), orientation=0):
        self.size = size
        self.pos = pos
        self.color = color
        self.scale = scale
        # self.rotation = 0
        self.shape = pg.Rect((0, 0), (32, 32))

    def draw(self, screen):
        self.shape.size = self.scale * self.size
        self.shape.center = (self.pos[0], screen.get_height( ) - self.pos[1])
        pg.draw.rect(screen, self.color, self.shape)

    def set_translation(self, pos=np.array([0, 0])):
        self.pos = pos.round()

    def set_scale(self, scale=np.array([1, 1])):
        self.scale = scale

    def set_color(self, color=np.array([255, 255, 255])):
        self.color = color
