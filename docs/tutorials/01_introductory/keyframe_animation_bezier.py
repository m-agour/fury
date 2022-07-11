"""
=====================
Keyframe animation
=====================

Keyframe animation explained with a simple tutorial

"""
import random

import numpy as np
from fury import actor, window, ui, utils
from fury.animation import Timeline, StepInterpolator, LinearInterpolator, \
    LABInterpolator, CubicSplineInterpolator, BezierInterpolator, HSVInterpolator, XYZInterpolator

scene = window.Scene()

showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)
showm.initialize()

# p0, p1, p2, 03
# p0 and p3 are the positions
# p1 is the control point for the point p0
# p2 is the control point for the point p3
points = [
    [-2, 0, 0],  # p0
    [-15, 6, 0],  # p1
    [27, 18, 0],  # p2
    [18, 0, 0],  # p3
]

# Visualizing points
pts_actor = actor.sphere(np.array([points[0], points[3]]), (1, 0, 0),
                         radii=0.3)
# Visualizing the control points
cps_actor = actor.sphere(np.array([points[1], points[2]]), (0, 0, 1),
                         radii=0.6)
# Visualizing the connection between the control points and the points
cline_actor = actor.line(np.array([points[0:2], points[2:4]]),
                         colors=np.array([0, 1, 0]))

mainTimeline = Timeline(main_timeline=True)
mainTimeline.play()
sphere = actor.sphere(np.array([[3, 4, 5]]), np.random.random([1, 3]), 0.3)
spheres = [actor.sphere(np.array([[0, 0, 0]]), np.random.random([1, 3]))]
# scene.add(sphere)

# creating the timeline
for i in range(80):

    actors = [actor.sphere(np.random.random([1, 3]) * 20,
                           np.random.random([1, 3]),
                           np.random.random([1, 1]))]
    timeline = Timeline(actors)

    for t in range(0, 100, 5):
        timeline.translate(t, np.random.random(3) * 30 - 15)
        timeline.scale(t, np.array([random.random()] * 3))
        timeline.set_color(t, np.random.random(3))
    # timeline.set_position_interpolator(CubicSplineInterpolator)

    mainTimeline.add_timeline(timeline)

# adding actors to the scene
scene.add(pts_actor, cps_actor, cline_actor, mainTimeline)


# making a function to update the animation
def timer_callback(_obj, _event):
    mainTimeline.update_animation()
    showm.render()


# Adding the callback function that updates the animation
showm.add_timer_callback(True, 10, timer_callback)

showm.start()
