"""
=====================
Keyframe animation
=====================

Tutorial on making keyframe-based animation in FURY using Spline interpolators.

"""

import numpy as np
from fury import actor, window
from fury.animation.timeline import Timeline
from fury.animation.interpolator import SplineInterpolator

# Creating the scene
scene = window.Scene()

# Creating a show manager
showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)
showm.initialize()

position_keyframes = {
    0: np.array([0, 0, 0]),
    2: np.array([10, 3, 5]),
    4: np.array([20, 14, 13]),
    6: np.array([-20, 20, 0]),
    8: np.array([17, -10, 15]),
    10: np.array([0, -6, 0]),
}

# Add dots to visualize the position keyframes
pos_dots = actor.dot(np.array(list(position_keyframes.values())))

# Creating a timeline
main_timeline = Timeline(playback_panel=Timeline)

# creating two timelines (one uses linear and the other uses' spline
# interpolator), each timeline controls a sphere actor
sphere_linear = actor.sphere(np.array([[0, 0, 0]]), (1, 0.5, 0.2), 0.5)
linear_tl = Timeline()
linear_tl.add(sphere_linear)

linear_tl.set_position_keyframes(position_keyframes)
# Note: LinearInterpolator is used by default. So, no need to set it.

sphere_spline = actor.sphere(np.array([[0, 0, 0]]), (0.3, 0.9, 0.6), 1)
spline_tl = Timeline(sphere_spline)
spline_tl.set_position_keyframes(position_keyframes)

# Setting 5th degree spline interpolator for position keyframes.
spline_tl.set_position_interpolator(SplineInterpolator, 5)

# Adding timelines to the main timeline (so that it controls their playback)
main_timeline.add([spline_tl, linear_tl])
# Now that these two timelines are added to main_timeline, if main_timeline
# is played, paused, ..., all these changes will reflect on the children
# timelines.

# Adding the main timeline to the scene along with the visualizing points.
scene.add(main_timeline, pos_dots)


# making a function to update the animation and render the scene
def timer_callback(_obj, _event):
    main_timeline.update_animation()
    showm.render()


# Adding the callback function that updates the animation
showm.add_timer_callback(True, 10, timer_callback)

showm.start()