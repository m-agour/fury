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

# arrow = actor.arrow(np.array([[0, 0, 0]]), directions=(1, 0, 0), colors=(255, 100, 1))


animation = AnimationSystem()

ruler = actor.arrow(np.array([
    [0, -1.6, 0],
    [5, -1.6, 0],
    [10, -1.6, 0],
    [15, -1.6, 0],
    [20, -1.6, 0]
]), directions=(0, 1, 0), colors=(0, 0, 1))

sphere = actor.sphere(np.array([[0, 0, 0]]), colors=(200, 2, 2), radii=0.6, use_primitive=False)

positions = np.array([[0.0, 0.0, 0.0], [20.0, 0.0, 0.0], [-20.0, 0.0, 0.0], [0.0, 15.0, 0.0]])
# key_circles = actor.sphere(positions.copy(), colors=(200, 0, 0), radii=0.1)

# arrow = actor.arrow(np.array([[0, 0, 0]]), directions=direction, colors=color, scales=(1, 1, 1))
anim_arrow = Animatable(sphere)

# anim_arrow.set_translation_interpolation_method(CUBIC_SPLINE)

for i in range(0, 90):
    anim_arrow.translate(1000 * (3 * i + 1), np.array([20, 0, 0]))
    anim_arrow.translate(1000 * (3 * i + 2), np.array([0, 15, 0]))
    anim_arrow.translate(1000 * (3 * i + 3), np.array([0, 0, 0]))

animation.add_animatable(anim_arrow)

[scene.add(i) for i in animation.get_actors()]

panel = ui.Panel2D(size=(100, 100), color=(1, 1, 1), align="right")
panel.center = (400, 50)

start_button = ui.Button2D(
    icon_fnames=[("square", read_viz_icons(fname="play3.png"))]
)

colors = vtkNamedColors()

last = 0

label = ui.TextBox2D(50, 50, 'None', position=(400, 700))


def update_animation_blocking():
    global last
    while 1:
        # last = time()
        if showm.lock_current():
            # ...
            animation.update()
        showm.release_current()
        # print(time() - last)

        # print(time() - last)


def update_animation_different_thread():
    global last
    while 1:
        last = time()
        animation.update()
        sleep(1 / 1200)


def update_animation_no_sleep():
    while 1:
        animation.update()


def play(i_ren, _obj, _button):
    animation.play()
    last = time()


panel.add_element(start_button, (0.5, 0.33))

start_button.on_left_mouse_button_clicked = play

scene.add(label)
scene.add(panel)
scene.add(ruler)

showm.initialize()

update_anim_thread = Thread(target=update_animation_blocking)
# update_anim_thread = Thread(target=update_animation_different_thread)
# update_anim_thread = Thread(target=update_animation_no_sleep)

update_anim_thread.start()
showm.start(multithreaded=1)

window.record(showm.scene, size=(900, 768),
              out_path="viz_solar_system_animation.png")

update_anim_thread.join()
