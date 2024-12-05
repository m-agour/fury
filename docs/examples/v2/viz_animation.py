from fury.v2.actor import glTF, sphere
from fury.v2.window import ShowManager, Scene, record
from fury.data import read_viz_cubemap, fetch_viz_cubemaps, fetch_gltf, read_viz_gltf
from fury.v2.io import load_cube_map_texture
from fury.v2.animation import Animation, spline_interpolator
import pygfx
import numpy as np
import asyncio
import math
import time
import numpy as np
from wgpu.gui.auto import WgpuCanvas, run
import pygfx as gfx
from fury.v2.actor import arrow, sphere, axis

np.random.seed(99999)


renderer = gfx.renderers.WgpuRenderer(WgpuCanvas())
scene = gfx.Scene()

spheres = sphere(centers=np.random.rand(1, 3) * 80 - 40,
                 colors=np.random.rand(1, 4), radii=5,
                 phi=30, theta=30, material='phong')

camera = pygfx.PerspectiveCamera(45, 640 / 480, width=1920, height=1080)
controller = pygfx.OrbitController(camera)


camera.show_object(spheres, view_dir=(1.8, -0.6, -2.7))
scene.add(camera)
scene.add(spheres)


show_m = ShowManager(scene=scene, title="FURY 2.0: GLTF with Skybox")
interactive = True

# 30 keyframes for the animation
anim = Animation(spheres)
position_keyframes = {
    0.0: np.array([0, 0, 0]),
    1.0: np.array([10, 30, 5]),
    2.0: np.array([20, 14, 13]),
    4.0: np.array([-20, 20, 0]),
    5.0: np.array([17, -10, 15]),
    7.0: np.array([0, -6, 0]),
    8.0: np.array([0, 13, 0]),
    10.0: np.array([10, 3, 5]),
    14.0: np.array([20, 14, 13]),
    20.0: np.array([-20, 20, 0])}

anim.set_position_keyframes(position_keyframes)
anim.set_position_interpolator(spline_interpolator, degree=5)

camera = gfx.PerspectiveCamera(45, 16 / 9)
camera.show_object(spheres)
controller = gfx.OrbitController(camera, register_events=renderer)


def animate():
    renderer.render(scene, camera)
    renderer.request_draw()
    anim.update_animation()

if __name__ == "__main__":
    renderer.request_draw(animate)
    run()