import random
from time import sleep
from threading import Thread

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

axis = actor.line([np.array([-10_000, 0, 0]), np.array([10_000, 0, 0])], (1, 1, 1))


animation = AnimationSystem()

for _ in range(1000):
    color = [random.randint(0, 255) for i in range(3)]
    direction = [random.random() * 2 - 1 for i in range(3)]
    arrow = actor.box(np.array([[0, 0, 0]]), directions=direction, colors=color, scales=(1, 1, 1))
    anim_arrow = Animatable(arrow)
    # anim_arrow.set_translation_interpolation_method(CUBIC_SPLINE)
    skipped = False
    for j in range(1000, 100_000, 10000):
        if random.random() < 0.5 and not skipped:
            skipped = True
            continue

        skipped = False
        x, y, z = [random.randint(-100000, 100000)/10 for i in range(3)]
        anim_arrow.translate(j, np.array([x, y, z]))

    for j in range(1000, 100_000, 10000):
        if random.random() < 0.7 and not skipped:
            skipped = True
            continue

        skipped = False
        x = random.randint(10, 500)
        anim_arrow.scale(j, np.array([x, x, x]))
    animation.add_animatable(anim_arrow)

[scene.add(i) for i in animation.get_actors()]

panel = ui.Panel2D(size=(100, 100), color=(1, 1, 1), align="right")
panel.center = (400, 50)

start_button = ui.Button2D(
    icon_fnames=[("square", read_viz_icons(fname="play3.png"))]
)

colors = vtkNamedColors()


def timer_callback_1(_obj, _event):
    animation.update()


def timer_callback_2(_obj, _event):
    showm.render()


def timer_callback_3(_obj, _event):
    animation.update()
    showm.render()


def play(i_ren, _obj, _button):
    animation.play()


panel.add_element(start_button, (0.5, 0.33))

start_button.on_left_mouse_button_clicked = play

scene.add(panel)
scene.add(axis)
# scene.add(key_circles)

showm.initialize()
# showm.add_timer_callback(True,  1000//60, timer_callback_1)
# showm.add_timer_callback(True,  1000//60, timer_callback_2)
showm.add_timer_callback(True,  1000//60, timer_callback_3)
showm.start()

window.record(showm.scene, size=(900, 768),
              out_path="gg.png")
