from fury.v2.window import ShowManager
import pygfx as gfx

show_m = ShowManager()

cube = gfx.Mesh(
    gfx.box_geometry(100, 100, 100),
    gfx.MeshPhongMaterial(color="red", pick_write=True),
)

show_m.scene.add(cube)


def screenshot(event):
    show_m.snapshot('snapshot.png')


cube.add_event_handler(screenshot, "click")

if __name__ == "__main__":
    show_m.render()
    show_m.start()
