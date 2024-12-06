import pygfx as gfx
from fury.v2.actor.materials import _create_line_material


def lines(
        positions,
        colors=(1, 1, 1, 1),
        thickness=5.0,
        opacity=1.0,
        color_mode='auto',
        material='base',
        enable_picking=True
):
    geo = gfx.Geometry(positions=positions, colors=colors)
    mat = _create_line_material(
        material, thickness, opacity, color_mode, enable_picking)
    obj = gfx.Line(geo, mat)
    return obj
