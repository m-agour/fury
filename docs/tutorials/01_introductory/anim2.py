import random

import vtk
from vtkmodules.vtkCommonColor import vtkNamedColors

from fury.data import read_viz_icons
from fury.libs.animatable import Animatable
from fury.libs.interpolation import CUBIC_SPLINE
from fury.libs.keyframe import *
from fury.libs.animation import *
import numpy as np
from fury import window, actor, utils, io, ui
import itertools

scene = window.Scene()

showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)

# arrow = actor.arrow(np.array([[0, 0, 0]]), directions=(1, 0, 0), colors=(255, 100, 1))


animation = AnimationSystem()


arrow = actor.sphere(np.array([[0, 0, 0]]), colors=(200, 2, 2), radii=3)

positions = np.array([[0.0, 0.0, 0.0], [20.0, 0.0, 0.0], [-20.0, 0.0, 0.0], [0.0, 15.0, 0.0]])
key_circles = actor.sphere(positions.copy(), colors=(200, 2, 2), radii=1)

# arrow = actor.arrow(np.array([[0, 0, 0]]), directions=direction, colors=color, scales=(1, 1, 1))
anim_arrow = Animatable(arrow)

# anim_arrow.set_translation_interpolation_method(CUBIC_SPLINE)

anim_arrow.translate(100, np.array([-20, 0, 0]))
anim_arrow.translate(200, np.array([20, 0, 0]))
anim_arrow.translate(300, np.array([0, 15, 0]))
anim_arrow.translate(400, np.array([0, 0, 0]))

animation.add_animatable(anim_arrow)


[scene.add(i) for i in animation.get_actors()]


panel = ui.Panel2D(size=(100, 100), color=(1, 1, 1), align="right")
panel.center = (400, 50)

start_button = ui.Button2D(
    icon_fnames=[("square", read_viz_icons(fname="play3.png"))]
)

colors = vtkNamedColors()

def timer_callback(_obj, _event):
    animation.update()
    # some stats
    for a in animation.get_actors():
        x = positions[0] - np.array(a.GetPosition())
        if np.sqrt(x.dot(x)) < 0.015:
            ...
            # print(a.GetPosition() , random.random())
    showm.render()


def play(i_ren, _obj, _button):
    animation.play()


panel.add_element(start_button, (0.5, 0.33))

start_button.on_left_mouse_button_clicked = play

scene.add(panel)
scene.add(key_circles)

showm.initialize()
showm.add_timer_callback(True,  1, timer_callback)
showm.start()

window.record(showm.scene, size=(900, 768),
              out_path="gg.png")
