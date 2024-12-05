import math
import time
import numpy as np
from wgpu.gui.auto import WgpuCanvas, run
import pygfx as gfx
from fury.v2.actor import arrow, sphere, axis

np.random.seed(99999)


renderer = gfx.renderers.WgpuRenderer(WgpuCanvas())
scene = gfx.Scene()

centers = np.random.rand(1000, 3) * 80 - 40
colors = np.random.rand(1000, 4)
colors[:, 3] = 1.0
radii = np.random.uniform(1, 2, 1000)
directions = np.random.rand(1000, 3) * 2 - 1



spheres = sphere(centers=centers, colors=colors, radii=radii, phi=30, theta=30, material='phong')
arrows = arrow(centers=centers, directions=directions, scales=radii * 7,
               colors=colors, material='phong', resolution=100)
ax = axis(centers=np.array([[0, 0, 0]]), scales=12)
scene.add(spheres)
scene.add(arrows)
scene.add(ax)

directional_light_up = gfx.DirectionalLight("#add8e6", 2)
directional_light_up.local.position = (1.5, 2.0, 1.0)
scene.add(directional_light_up)

directional_light_down = gfx.DirectionalLight("#ffd700", 0.4)
directional_light_down.local.position = (-1.5, -2.0, -1.0)
scene.add(directional_light_down)



camera = gfx.PerspectiveCamera(45, 16 / 9)
camera.show_object(spheres)
camera.local.position = [-27, 42.5, 425]
camera.look_at([0, 0, 0])
controller = gfx.OrbitController(camera, register_events=renderer)

last_t = time.time()

original_arrow_colors = arrows.geometry.colors.view.copy()
original_sphere_positions = spheres.geometry.positions.view.copy()
original_arrow_positions = arrows.geometry.positions.view.copy()
offset_spheres = spheres.geometry.colors.view.shape[0] // centers.shape[0]
offset_arrows = arrows.geometry.colors.view.shape[0] // centers.shape[0]


start_t = time.time()

def animate():
    global last_t, original_arrow_colors, arrows, spheres, centers, original_sphere_positions, \
        original_arrow_positions, directions, offset_spheres, offset_arrows, start_t
    renderer.render(scene, camera)
    renderer.request_draw()

    if last_t + 0.01 < time.time():
        last_t = time.time()

        spheres.geometry.colors.view[:,:] = np.repeat(colors +
                                                      np.random.rand(centers.shape[0], 4) * 0.4 - 0.1, offset_spheres,
                                                      axis=0)
        spheres.geometry.colors.view[:, 3] = 1.0
        spheres.geometry.colors.update_full()


        if start_t + 10 < time.time():
            start_t = time.time()
            spheres.geometry.positions.view[:, :] = original_sphere_positions
            arrows.geometry.positions.view[:, :] = original_arrow_positions

        else:
            spheres.geometry.positions.view[:, :] = (original_sphere_positions +
                                                     np.repeat(directions, offset_spheres, axis=0) *
                                                     (np.exp(time.time() - start_t) / 10 + np.sin(time.time())))

            arrows.geometry.positions.view[:, :] = (original_arrow_positions +
                                                    np.repeat(directions, offset_arrows, axis=0) *
                                                    (np.exp(time.time() - start_t) / 10 + np.sin(time.time())))

        arrows.geometry.colors.view[:, 1] = original_arrow_colors[:, 1] * (np.sin(time.time()) + 2) / 3
        arrows.geometry.colors.update_full()


    spheres.geometry.positions.update_full()
    arrows.geometry.positions.update_full()

    arrows.geometry.colors.view[:,1] = original_arrow_colors[:, 1] * (np.sin(time.time()) + 2) / 3
    arrows.geometry.colors.update_full()

print(arrows)

if __name__ == "__main__":
    renderer.request_draw(animate)
    run()