"""
=====================
Keyframe animation
=====================

Keyframe animation explained with a simple tutorial

"""
import numpy as np
from fury import actor, window, ui, utils
from fury.animation import Timeline, StepInterpolator, LinearInterpolator, \
    LABInterpolator, CubicSplineInterpolator, \
    CompositeTimeline, BezierInterpolator, HSVInterpolator, XYZInterpolator

scene = window.Scene()

showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)
showm.initialize()


timelines = CompositeTimeline()
sphere = actor.sphere(np.array([[3, 4, 5]]), np.random.random([1, 3]), 0.3)
# spheres = [actor.sphere(np.random.random((1, 3)) * 15, np.random.random((1, 3)), np.random.random((1, 1)))]
spheres = [actor.sphere(np.array([[0, 0, 0]]), np.random.random([1, 3]))]
# scene.add(sphere)

# creating the timeline
for i in range(1):

    actors = [actor.sphere(np.random.random([1, 3]) * 20,
                              np.random.random([1, 3]),
                              np.random.random([1, 1])) for _ in range(100)]
    timeline = Timeline(actors, using_shaders=0)


    for t in range(0, 100, 5):
        timeline.translate(t, np.random.random(3) * 30 - 15)
        # timeline.scale(t, np.random.random(3))
        timeline.set_color(t, np.random.random(3))
    # timeline.set_position_interpolator(CubicSplineInterpolator)

    timelines.add_timeline(timeline)


# adding actors to the scene
scene.add(pts_actor, cps_actor, cline_actor, timelines)


# making a function to update the animation
def timer_callback(_obj, _event):
    timelines.update_animation()
    showm.render()


# Adding the callback function that updates the animation
showm.add_timer_callback(True, 10, timer_callback)

showm.start()
