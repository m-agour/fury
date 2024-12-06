import pygfx as gfx
from fury.v2.actor import sphere


def points(radius, point_positions, colors, position=(0, 0, 0)):
    group = gfx.Group()

    for i in range(len(point_positions)):
        group.add(
            sphere(
                radius=radius,
                color=colors[i],
                position=point_positions[i]
            )
        )

    group.local.position = position
    return group
