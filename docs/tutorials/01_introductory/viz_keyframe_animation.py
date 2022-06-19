import numpy as np
from fury import actor, window, ui
from fury.animation import Timeline, StepInterpolator, LinearInterpolator
from fury.data import read_viz_icons

scene = window.Scene()

showm = window.ShowManager(scene,
                           size=(900, 768), reset_camera=False,
                           order_transparent=True)
showm.initialize()

panel = ui.Panel2D(size=(250, 40), color=(1, 1, 1), align="right")
panel.center = (460, 40)

pause_btn = ui.Button2D(
    icon_fnames=[("square", read_viz_icons(fname="pause2.png"))]
)
stop_btn = ui.Button2D(
    icon_fnames=[("square", read_viz_icons(fname="stop2.png"))]
)
start_btn = ui.Button2D(
    icon_fnames=[("square", read_viz_icons(fname="play3.png"))]
)

# Add the buttons on the panel

panel.add_element(pause_btn, (0.15, 0.15))
panel.add_element(start_btn, (0.45, 0.15))
panel.add_element(stop_btn, (0.75, 0.15))

arrow = actor.cube(np.array([[0, 0, 0]]), np.array([[1, 1, 1]]))
walls = actor.square(np.array([[-7, 0, -4], [7, 0, -4], [0, 0, -4]]),
                     np.array([[-1, 0, 1], [-1, 0, -1], [0, 0, 0]]),
                     colors=np.array([[1, 1, 1]]), scales=50)
cnt = 0


def timer_callback(_obj, _event):
    global cnt
    cnt += 1
    timeline.update()
    showm.render()


def start_animation(i_ren, _obj, _button):
    timeline.play()


def pause_animation(i_ren, _obj, _button):
    timeline.pause()


def stop_animation(i_ren, _obj, _button):
    timeline.stop()


start_btn.on_left_mouse_button_clicked = start_animation
pause_btn.on_left_mouse_button_clicked = pause_animation
stop_btn.on_left_mouse_button_clicked = stop_animation

scene.add(arrow)
scene.add(walls)
scene.add(panel)

timeline = Timeline([arrow])

timeline.translate(0, np.array([0, 0, 0]))
timeline.translate(5, np.array([-12, 11, 0]))
timeline.translate(15, np.array([12, -11, 0]))

timeline.set_scale_interpolator(StepInterpolator)

timeline.scale(0, np.array([5, 5, 5]))
timeline.scale(3, np.array([3, 3, 3]))
timeline.scale(6, np.array([2, 2, 2]))
timeline.scale(15, np.array([5, 5, 5]))

timeline.set_color(0, np.array([1, 0, 0]))
timeline.set_color(7, np.array([1, 0, 0]))

timeline.set_keyframes(17, {
    "position": np.array([0, 0, 0]),
    "scale": np.array([1, 1, 1])
})

showm.add_timer_callback(True, 10, timer_callback)

showm.start()
