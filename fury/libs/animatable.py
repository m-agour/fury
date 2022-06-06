import numpy as np
from vtkmodules.vtkRenderingCore import vtkActor

from fury.libs.interpolation import LINEAR
from fury.libs.keyframe import Keyframe
from fury.libs.timeline import TranslateTimeline, ScaleTimeline, ColorTimeline


class Animatable:
    def __init__(self, actor: vtkActor):
        self.actor = actor
        self.translateTimeline = TranslateTimeline(1, 1, method=LINEAR)
        self.scaleTimeline = ScaleTimeline(1, 1, method=LINEAR)
        self.colorTimeline = ColorTimeline(1, 1, method=LINEAR)
        self.footsteps = []

    def translate(self, timestamp=0, destination=np.array([0, 0, 0])):
        self.translateTimeline.addKeyframe(Keyframe(timestamp, destination))

    def set_color(self, timestamp=0, color=np.array([255, 255, 255])):
        self.colorTimeline.addKeyframe(Keyframe(timestamp, color))

    def scale(self, timestamp=0, scale=np.array([0, 0, 0])):
        self.scaleTimeline.addKeyframe(Keyframe(timestamp, scale))

    def update(self, t):
        self.actor.SetPosition(*self.translateTimeline.get_pos(t))
        self.actor.SetScale(*self.scaleTimeline.get_scale(t))
        # self.actor.set_scale((self.scaleTimeline.get_scale(t)))

    def get_actor(self):
        return self.actor

    def clear_footsteps(self):
        self.translateTimeline.clear_footsteps()
        self.scaleTimeline.clear_footsteps()
        self.colorTimeline.clear_footsteps()

    def get_translation_interpolation_method(self):
        return self.translateTimeline.get_interpolation_method()

    def set_translation_interpolation_method(self, method):
        return self.translateTimeline.set_interpolation_method(method)

    def is_active(self, t_ms):
        return min(self.translateTimeline.timestamps) <= t_ms <= max(self.translateTimeline.timestamps)

    def reset(self, t_ms):
        return min(self.translateTimeline.timestamps) <= t_ms <= max(self.translateTimeline.timestamps)