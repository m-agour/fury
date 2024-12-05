###############################################################################
# This example demonstrates how to create a 3D scene in FURY featuring a GLTF
# model with Physically-Based Rendering (PBR) materials and a skybox environment.
# We’ll load a GLTF model (a "DamagedHelmet" in this example) and apply a
# skybox environment map, allowing the model’s materials to reflect the
# surrounding scene for enhanced realism. Additionally, a spotlight and a
# perspective camera are added to complete the setup.

from fury.v2.actor import glTF
from fury.v2.window import ShowManager, Scene, record
from fury.data import read_viz_cubemap, fetch_viz_cubemaps, fetch_gltf, read_viz_gltf
from fury.v2.io import load_cube_map_texture
import pygfx

###############################################################################
# Fetch and set up the skybox textures.
fetch_viz_cubemaps()
texture_files = read_viz_cubemap("skybox")
cube_map = load_cube_map_texture(texture_files)

###############################################################################
# Create a Scene object and pass the skybox texture to it.
scene = Scene(skybox=cube_map)

###############################################################################
# Download and load the GLTF model file.
# Here, we use a sample model called "DamagedHelmet."
# GLTF files often support Physically-Based Rendering (PBR),
# which simulates realistic lighting and material interactions.
# By setting `cube_map` as the environment map, the GLTF model
# reflects the surrounding environment.
fetch_gltf("DamagedHelmet")
gltf_path = read_viz_gltf("DamagedHelmet")
gltf = glTF(gltf_path, cube_map)
scene.add(gltf)


###############################################################################
# Add a spotlight to the scene.
light = pygfx.SpotLight(color=(1, 1, 1), intensity=10)
light.local.position = (-1.5, -0.23,  -3)
scene.add(light)

###############################################################################
# Set up a perspective camera for the scene.
camera = pygfx.PerspectiveCamera(45, 640 / 480, width=1920, height=1080)
controller = pygfx.OrbitController(camera)
camera.show_object(gltf, view_dir=(1.8, -0.6, -2.7))
scene.add(camera)

###############################################################################
# Initialize the ShowManager to display the scene in a window.
show_m = ShowManager(scene=scene, title="FURY 2.0: GLTF with Skybox")
interactive = True
print(gltf)
if __name__ == "__main__":
    if interactive:
        show_m.start()
    else:
        record(scene, "gltf_skybox_scene.png")
