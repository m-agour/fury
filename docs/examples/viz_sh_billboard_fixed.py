"""Optimized SH Billboard Visualization with LUT."""
from __future__ import annotations

import sys
sys.path.insert(0, '/home/moabouag/dev/fury')

import numpy as np
from fury import actor, window

l_max = 8
use_lut = True
use_gpu_nn = False
use_bicubic = True
n_glyphs = 60000

def generate_controlled_symmetric_shapes(n_glyphs: int, l_max: int = 8) -> np.ndarray:
    """Generate SH coefficients with controlled symmetric shapes."""
    n_coeffs = (l_max + 1) ** 2
    coeffs = np.zeros((n_glyphs, n_coeffs), dtype=np.float32)
    
    for i in range(n_glyphs):
        base_intensity = 0.5 + 0.2 * np.sin(i * 0.1)
        coeffs[i, 0] = base_intensity
        
        shape_type = i % (2 * l_max + 1)
        phase = i * 0.08
        
        if l_max >= 1 and shape_type < 3:
            if shape_type == 0:
                coeffs[i, 2] = 0.3 * np.cos(phase)
            elif shape_type == 1:
                coeffs[i, 1] = 0.25 * np.sin(phase)
                coeffs[i, 3] = 0.25 * np.sin(phase)
            elif shape_type == 2:
                coeffs[i, 1] = 0.25 * np.cos(phase)
                coeffs[i, 3] = -0.25 * np.cos(phase)
        
        if l_max >= 2 and 3 <= shape_type < 8:
            rel_shape = shape_type - 3
            if rel_shape == 0:
                coeffs[i, 6] = 0.4 * np.sin(phase + 1)
            elif rel_shape == 1:
                coeffs[i, 6] = -0.4 * np.cos(phase + 1)
            elif rel_shape == 2:
                coeffs[i, 8] = 0.3 * np.sin(phase + 2)
            elif rel_shape == 3:
                coeffs[i, 4] = 0.3 * np.cos(phase + 2)
            elif rel_shape == 4:
                coeffs[i, 5] = 0.2 * np.sin(phase + 3)
                coeffs[i, 7] = 0.2 * np.sin(phase + 3)
        
        if l_max >= 3 and 8 <= shape_type < 15:
            rel_shape = shape_type - 8
            octupole_strength = 0.25
            if rel_shape == 0:
                coeffs[i, 12] = octupole_strength * np.cos(phase + 4)
            elif rel_shape == 1:
                coeffs[i, 9] = octupole_strength * np.sin(phase + 5)
                coeffs[i, 15] = octupole_strength * np.sin(phase + 5)
            elif rel_shape == 2:
                coeffs[i, 10] = 0.2 * np.cos(phase + 6)
                coeffs[i, 14] = 0.2 * np.cos(phase + 6)
            elif rel_shape < 6:
                coeffs[i, 11] = 0.15 * np.sin(phase + rel_shape)
                coeffs[i, 13] = 0.15 * np.sin(phase + rel_shape)
        
        if l_max >= 4:
            for l in range(4, l_max + 1):
                l_start_idx = l * l
                l_strength = 0.15 / l
                
                if shape_type % (l + 1) == 0:
                    m0_idx = l_start_idx + l
                    if m0_idx < n_coeffs:
                        coeffs[i, m0_idx] = l_strength * np.cos(phase + l)
                
                for m in range(1, min(l + 1, 3)):
                    if (shape_type + m) % (l + 2) == 0:
                        neg_m_idx = l_start_idx + l - m
                        pos_m_idx = l_start_idx + l + m
                        if pos_m_idx < n_coeffs:
                            coeff_val = l_strength * np.sin(phase + l + m)
                            coeffs[i, neg_m_idx] = coeff_val
                            coeffs[i, pos_m_idx] = coeff_val
    
    return coeffs


def create_optimized_glyphs(scene, n_glyphs, use_lut=True, use_nn=False, max_glyphs_per_actor=8000):
    """Create SH billboard glyphs with optimizations."""
    grid_size = int(np.ceil(np.sqrt(n_glyphs)))
    spacing = 1.0
    
    positions = np.zeros((n_glyphs, 3), dtype=np.float32)
    for i in range(n_glyphs):
        x_idx = i % grid_size
        y_idx = i // grid_size
        positions[i, 0] = x_idx * spacing - grid_size * spacing / 2
        positions[i, 1] = y_idx * spacing - grid_size * spacing / 2
        positions[i, 2] = 0.0
    
    coeffs = generate_controlled_symmetric_shapes(n_glyphs, l_max=l_max)
    
    if n_glyphs <= max_glyphs_per_actor:
        glyph = actor.sph_glyph_billboard(
            coeffs,
            centers=positions,
            color_type="standard",
            scale=2,
            l_max=l_max,
            opacity=1.0,
            use_precomputation=use_lut,
            use_bicubic=use_bicubic
        )
        scene.add(glyph)
    else:
        n_actors = int(np.ceil(n_glyphs / max_glyphs_per_actor))
        
        for actor_idx in range(n_actors):
            start_idx = actor_idx * max_glyphs_per_actor
            end_idx = min(start_idx + max_glyphs_per_actor, n_glyphs)
            
            glyph = actor.sph_glyph_billboard(
                coeffs[start_idx:end_idx],
                centers=positions[start_idx:end_idx],
                color_type="standard",
                scale=2,
                l_max=l_max,
                opacity=1.0,
                use_precomputation=use_lut,
                use_bicubic=use_bicubic
            )
            scene.add(glyph)


if __name__ == "__main__":
    scene = window.Scene()
    scene.background = (0.02, 0.02, 0.05)
    
    create_optimized_glyphs(scene, n_glyphs, use_lut=use_lut, use_nn=use_gpu_nn)
    
    showm = window.ShowManager(
        scene=scene,
        size=(1600, 1200),
        title=f"SH Billboards - {n_glyphs:,} glyphs"
    )
    showm.start()
