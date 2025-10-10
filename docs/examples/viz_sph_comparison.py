"""
Spherical Harmonics: Mesh vs Billboard Comparison
"""

import numpy as np
from fury import actor, window

coefficients = np.zeros((1, 1, 1, 16), dtype=np.float32)
coefficients[0, 0, 0, 0] = 1.0      # l=0, m=0
coefficients[0, 0, 0, 1] = 0.8      # l=1, m=-1
coefficients[0, 0, 0, 2] = 0.6      # l=1, m=0
coefficients[0, 0, 0, 3] = 0.8      # l=1, m=1
coefficients[0, 0, 0, 4] = 0.4      # l=2, m=-2
coefficients[0, 0, 0, 5] = 0.7      # l=2, m=-1
coefficients[0, 0, 0, 6] = 0.9      # l=2, m=0
coefficients[0, 0, 0, 7] = 0.7      # l=2, m=1
coefficients[0, 0, 0, 8] = 0.4      # l=2, m=2
coefficients[0, 0, 0, 9] = 0.3      # l=3, m=-3
coefficients[0, 0, 0, 10] = 0.5     # l=3, m=-2
coefficients[0, 0, 0, 11] = 0.6     # l=3, m=-1
coefficients[0, 0, 0, 12] = 0.8     # l=3, m=0
coefficients[0, 0, 0, 13] = 0.6     # l=3, m=1
coefficients[0, 0, 0, 14] = 0.5     # l=3, m=2
coefficients[0, 0, 0, 15] = 0.3     # l=3, m=3

sph_glyph_mesh = actor.sph_glyph(
    coefficients,
    sphere=(50, 50),
    color_type="orientation"
)
sph_glyph_mesh.position = (0.0, 0.0, 0.0)

centers = np.array([[4.0, 0.0, 0.0]], dtype=np.float32)

sph_glyph_billboard = actor.sph_glyph_billboard(
    coefficients,
    centers=centers,
    color_type="orientation",
    use_precomputation=True
)

mesh_label = actor.text(
    "MESH",
    position=(-0.5, -2.5, 0),
    font_size=0.5,
)

billboard_label = actor.text(
    "BILLBOARD",
    position=(3.5, -2.5, 0),
    font_size=0.5,
)

title_text = actor.text(
    "Spherical Harmonics Comparison",
    position=(2, 3.0, 0),
    font_size=0.6,
)

performance_text = actor.text(
    "Same result - Billboard 5-15x faster",
    position=(2, 2.5, 0),
    font_size=0.4,
)

scene = window.Scene()
scene.add(
    sph_glyph_mesh,
    sph_glyph_billboard,
    mesh_label,
    billboard_label,
    title_text,
    performance_text,
)


show_m = window.ShowManager(
    scene=scene,
    size=(1000, 500),
    title="FURY: Perfect Symmetric SH Comparison"
)


show_m.start()