from vtkmodules.vtkCommonColor import vtkNamedColors
from fury.data import read_viz_icons
from fury.libs.animatable import Animatable

from fury.libs.animation import *
import numpy as np
from fury import window, actor, utils, io, ui
import itertools

scene = window.Scene()

showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)

# arrow = actor.arrow(np.array([[0, 0, 0]]), directions=(1, 0, 0), colors=(255, 100, 1))


animation = AnimationSystem(300)

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


for i in range(0, 90, 2):
    h = 0
    l = 20
    anim_arrow.translate(1000 * (i), np.array([0, 0, 0]))
    anim_arrow.translate(1000 * (i+1), np.array([20, 0, 0]))



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
    # some stats
    # away = True
    # for a in animation.get_actors():
    #     for i, position in enumerate(positions):
    #         x = position - np.array(a.GetPosition())
    #         if np.sqrt(x.dot(x)) < 0.15:
    #             if away:
    #                 # print("Passed", i)
    #                 away = 0
    #         else:
    #             away = True


def timer_callback_2(_obj, _event):
    showm.render()

    # animation.pause()
    # window.record(showm.scene, size=(900, 768),
    #               out_path=f"out/{int(animation.get_current_timestamp())}.png")
    # animation.play()


def timer_callback_3(_obj, _event):
    animation.update()
    showm.render()
    # window.record(showm.scene, size=(900, 768),
    #               out_path=f"{animation.get_current_timestamp()}.png")


def play(i_ren, _obj, _button):
    animation.play()


panel.add_element(start_button, (0.5, 0.33))

start_button.on_left_mouse_button_clicked = play

scene.add(panel)
# scene.add(key_circles)
scene.add(ruler)

showm.initialize()
# showm.add_timer_callback(True,  10, timer_callback_1)
# showm.add_timer_callback(True,  10, timer_callback_2)
showm.add_timer_callback(True,  10, timer_callback_3)
showm.start()

window.record(showm.scene, size=(900, 768),
              out_path="gg.png")
