from vtkmodules.vtkCommonColor import vtkNamedColors
from fury.data import read_viz_icons
from fury.libs.animatable import Animatable

from fury.libs.animation import *
import numpy as np
from fury import window, actor, utils, io, ui
import itertools
from time import perf_counter

scene = window.Scene()

showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)

# arrow = actor.arrow(np.array([[0, 0, 0]]), directions=(1, 0, 0), colors=(255, 100, 1))


animation = AnimationSystem(300)

sphere_1 = actor.sphere(np.array([[0, 0, 0]]), colors=(1, 0, 0), radii=0.6)
sphere_2 = actor.sphere(np.array([[0, 0, 0]]), colors=(0, 1, 0), radii=0.6)

positions = np.array([[0.0, 0.0, 0.0], [20.0, 0.0, 0.0], [-20.0, 0.0, 0.0], [0.0, 15.0, 0.0]])
# key_circles = actor.sphere(positions.copy(), colors=(200, 0, 0), radii=0.1)

# arrow = actor.arrow(np.array([[0, 0, 0]]), directions=direction, colors=color, scales=(1, 1, 1))
anim_sphere_1 = Animatable(sphere_1)
anim_sphere_2 = Animatable(sphere_2)

# anim_arrow.set_translation_interpolation_method(CUBIC_SPLINE)
i = 1000
anim_sphere_1.translate(0, np.array([1.8, 0, 0]))
anim_sphere_2.translate(0, np.array([-1.8, 0, 0]))
anim_sphere_1.translate(1 * i, np.array([0.6, 0, 0]))
anim_sphere_2.translate(1 * i, np.array([-0.6, 0, 0]))
anim_sphere_1.translate(2 * i, np.array([1.8, 0, 0]))
anim_sphere_2.translate(2 * i, np.array([-1.8, 0, 0]))

animation.add_animatable(anim_sphere_1)
animation.add_animatable(anim_sphere_2)

[scene.add(i) for i in animation.get_actors()]

panel = ui.Panel2D(size=(100, 100), color=(1, 1, 1), align="right")
panel.center = (400, 50)

start_button = ui.Button2D(
    icon_fnames=[("square", read_viz_icons(fname="play3.png"))]
)

colors = vtkNamedColors()

min_dist = 10
last = 0
start_t = 0


def timer_callback(_obj, _event):
    global min_dist, last
    t = time()
    print(t - last)
    last = t
    # animation.update()
    # s1, s2 = animation.get_actors()
    # dis = s1.GetPosition()[0] - 0.6
    # if dis < min_dist:
    #     min_dist = dis
    #     t = time() - start_t
    #     print(f"Closest distance is {min_dist} at time {t} with error {0}")
    # showm.render()


def play(i_ren, _obj, _button):
    global start_t, last
    animation.play()


times = []


def callb(_obj, _event):
    global last
    if last:
        times.append(perf_counter()-last)
    last = perf_counter()


def s(_obj, _event):
    global times
    print(times[-1])


panel.add_element(start_button, (0.5, 0.33))

start_button.on_left_mouse_button_clicked = play

scene.add(panel)

showm.initialize()

showm.add_timer_callback(True, 1014, callb)
showm.add_timer_callback(True, 7000, s)
showm.start()
