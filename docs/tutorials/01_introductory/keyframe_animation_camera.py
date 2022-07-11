"""
=====================
Keyframe animation
=====================

Keyframe animation explained with a simple tutorial

"""
import random

import numpy as np
from fury import actor, window
from fury.animation import Timeline, HSVInterpolator, LABInterpolator, \
    CubicSplineInterpolator

scene = window.Scene()

showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)
showm.initialize()

main_timeline = Timeline(playback_panel=True)

arrow = actor.arrow(np.array([[0, 0, 0]]), np.array([[0, 1, 0]]),
                    np.array([[1, 1, 0]]), scales=5)
plan = actor.box(np.array([[0, 0, 0]]), colors=np.array([[1, 1, 1]]),
                 scales=np.array([[20, 0.2, 20]]))

for i in range(50):

    actors = [actor.sphere(np.random.random([1, 3]) * 20,
                           np.random.random([1, 3]),
                           np.random.random([1, 3]))]
    timeline = Timeline(actors, using_shaders=0)

    for t in range(0, 100, 5):
        timeline.translate(t, np.random.random(3) * 30 - np.array([15, 10, 15]))
        timeline.scale(t, np.array([random.random()] * 3))
        timeline.set_color(t, np.random.random(3))

    timeline.set_color_interpolator(HSVInterpolator)
    timeline.set_position_interpolator(CubicSplineInterpolator)

    main_timeline.add_timeline(timeline)

# adding actors to the scene
scene.add(main_timeline, arrow, plan)

main_timeline.set_camera_position(0, np.array([3, 3, 3]))
main_timeline.set_camera_position(4, np.array([50, 25, -40]))
main_timeline.set_camera_position(10, np.array([-50, 50, -40]))
main_timeline.set_camera_position(14, np.array([-25, 25, -20]))

main_timeline.set_camera_focal(15, np.array([0, 0, 0]))
main_timeline.set_camera_focal(22, np.array([3, 9, 12]))
main_timeline.set_camera_focal(25, np.array([7, 5, 3]))
main_timeline.set_camera_focal(30, np.array([-2, 9, -6]))
main_timeline.set_camera_focal(40, np.array([5, 15, 3]))
main_timeline.set_camera_focal(50, np.array([0, 17, 0]))
main_timeline.set_camera_position(70, np.array([-50, 25, -50]))


main_timeline.set_camera_position_interpolator(CubicSplineInterpolator)
main_timeline.set_camera_focal_interpolator(CubicSplineInterpolator)


# making a function to update the animation
def timer_callback(_obj, _event):
    main_timeline.update_animation()
    showm.render()


# Adding the callback function that updates the animation
showm.add_timer_callback(True, 10, timer_callback)

showm.start()
