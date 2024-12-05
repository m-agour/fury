import numpy as np
from fury.v2.window import ShowManager, Scene, record
from fury.v2.actor import sphere, cylinder, arrow, box



scene = Scene()


sphere_actor = sphere(centers=np.array([[0, 0, 0]]), colors=(1, 0, 0), radii=3.0)
cylinder_actor = cylinder(centers = np.array([[4, 0, 0]]), directions=np.array([[0, 1, 0]]), colors = (0, 1, 0),
                          heights = 7.0, radius=0.3, resolution=100, capped=True)
arrow_actor = arrow(centers=np.array([[6, 0, 0]]), directions=np.array([[0, 1, 0]]), colors=(0, 0, 1), scales=10.0)
box_actor = box(centers=np.array([[10, 0, 0]]),  colors=(1, 0, 1), scales=(3, 3, 3))

scene.add(sphere_actor)
scene.add(cylinder_actor)
scene.add(arrow_actor)
scene.add(box_actor)


show_m = ShowManager(scene=scene, title="FURY 2.0: Skybox Example")

interactive = True

if __name__ == "__main__":

    if interactive:
        show_m.start()
    else:
        record(scene, "actors.png")
