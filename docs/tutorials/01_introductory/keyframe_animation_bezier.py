"""
=====================
Keyframe animation
=====================

Keyframe animation explained with a simple tutorial

"""
import random

import numpy as np
from vtkmodules.vtkRenderingCore import vtkActorCollection, vtkAssembly

from fury import actor, window, ui, utils
from fury.animation import Timeline, StepInterpolator, LinearInterpolator, \
    LABInterpolator, CubicSplineInterpolator, \
    CompositeTimeline, BezierInterpolator, HSVInterpolator, XYZInterpolator
from fury.data import read_viz_icons
from fury.ui.elements import PlaybackPanel
from fury.utils import get_polydata_colors

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

timelines = CompositeTimeline()
sphere = actor.sphere(np.array([[0, 0, 0]]), np.random.random([1, 3]))
scene.add(sphere)

# creating the timeline
t = Timeline(sphere)
playbackPanel = PlaybackPanel(timelines)

t.translate(0, np.array(points[0]), post_cp=np.array(points[1]))
t.scale(0, np.array([1, 1, 1]))
t.set_color(0, np.array([1, 0, 1]))

t.translate(3, np.array(points[3]), pre_cp=np.array(points[2]))
t.scale(3, np.array([2, 3, 1]))
t.set_color(3, np.array([0, 1, 1]))

# t.translate(6, np.array(points[0]))

t.set_position_interpolator(BezierInterpolator)
t.set_color_interpolator(XYZInterpolator)

timelines.add_timeline(t)


# adding actors to the scene
scene.add(playbackPanel, pts_actor, cps_actor, cline_actor)


# making a function to update the animation
def timer_callback(_obj, _event):
    timelines.update()
    playbackPanel._progress_bar.value = timelines.get_current_timestamp() * 100 / \
                            timelines.last_timestamp
    showm.render()


a = actor.square(np.array([[6, 6, 6]]))
actors = vtkAssembly()
actors.GetShaderProperty().GetVertexCustomUniforms().SetUniformf('time', 2)

scene.add(actors)
actors.SetPosition(100, 0, 0)

# Adding the callback function that updates the animation
showm.add_timer_callback(True, 10, timer_callback)

showm.start()
