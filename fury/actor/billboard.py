"""Billboard actor module.

Minimal isolated implementation of billboard support to reduce diffs in
existing planar actor module. Provides a Mesh-based world object and a
factory function plus shader registration.
"""

from __future__ import annotations

import numpy as np
import wgpu
from pathlib import Path

from fury.geometry import buffer_to_geometry
from fury.lib import Buffer, Mesh, register_wgpu_render_function
from fury.material import (
    BillboardMaterial,
    BillboardSphereMaterial,
    SphGlyphMaterial,
    validate_opacity,
)
import fury.primitive as fp
from fury.utils import create_sh_basis_matrix, get_lmax, get_n_coeffs


# Global cache for spherical harmonics precomputed lookup tables
_SH_PRECOMPUTE_CACHE = {}
_MAX_GPU_LUT_GLYPHS = 40000

# Cache for GPU device limits to avoid repeated queries
_GPU_DEVICE_LIMITS_CACHE = {}

def _get_gpu_max_buffer_size():
    """Get the maximum buffer size supported by the GPU device.
    
    Returns the device's max_buffer_size in bytes. Caches the result to avoid
    repeated device queries. Falls back to conservative 256 MB if query fails.
    
    Typical values:
    - Desktop GPUs: 2 GB (2^31 bytes)
    - WebGPU/WebGL: 256 MB - 1 GB  
    - Mobile: 128 MB - 512 MB
    """
    if 'max_buffer_size' in _GPU_DEVICE_LIMITS_CACHE:
        return _GPU_DEVICE_LIMITS_CACHE['max_buffer_size']
    
    try:
        adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
        device = adapter.request_device_sync()
        device_limits = device.limits
        max_size = device_limits.get('max_buffer_size', 256 * 1024 * 1024)
        _GPU_DEVICE_LIMITS_CACHE['max_buffer_size'] = max_size
        return max_size
    except Exception:
        default_size = 256 * 1024 * 1024  # 256 MB
        _GPU_DEVICE_LIMITS_CACHE['max_buffer_size'] = default_size
        return default_size


def _select_lut_resolution(l_max: int, glyph_count: int, base_resolution: tuple[int, int]) -> tuple[int, int]:
    """Choose a LUT resolution that balances quality, workload, and GPU buffer limits.
    
    Queries the actual GPU device to get max buffer size (typically 2 GB on desktop,
    but can be lower on WebGPU/mobile devices).
    
    LUT buffer size: glyph_count × phi_res × theta_res × 4 bytes
    """

    phi_res, theta_res = base_resolution
    
    # Get actual device buffer limit (cached after first call)
    max_buffer_bytes = _get_gpu_max_buffer_size()
    bytes_per_sample = 4  # float32
    
    # Calculate required buffer size with current resolution
    required_bytes = glyph_count * phi_res * theta_res * bytes_per_sample
    
    # If buffer too large, aggressively reduce resolution
    # Minimum: 64×32 for decent quality (smoothstep interpolation helps at low res)
    while required_bytes > max_buffer_bytes and (phi_res > 64 or theta_res > 32):
        # Reduce by factors of 2
        phi_res = max(64, phi_res // 2)
        theta_res = max(32, theta_res // 2)
        required_bytes = glyph_count * phi_res * theta_res * bytes_per_sample
    
    # For large batches, reduce resolution to avoid huge upfront cost
    # But maintain minimum 64×32 for smooth appearance with smoothstep interpolation
    if glyph_count > 8000 and required_bytes > max_buffer_bytes * 0.8:
        phi_res = min(phi_res, 64)
        theta_res = min(theta_res, 32)
    elif glyph_count > 6000 and required_bytes > max_buffer_bytes * 0.8:
        phi_res = min(phi_res, 64)
        theta_res = min(theta_res, 32)
    elif glyph_count > 4000 and required_bytes > max_buffer_bytes * 0.8:
        phi_res = min(phi_res, 96)
        theta_res = min(theta_res, 48)

    # Higher orders benefit from more samples – but respect buffer limit
    if l_max >= 6:
        phi_res = min(max(phi_res, 128), phi_res)  # Don't exceed current
        theta_res = min(max(theta_res, 64), theta_res)
    elif l_max >= 4:
        phi_res = min(max(phi_res, 96), phi_res)
        theta_res = min(max(theta_res, 48), theta_res)

    # Final check: ensure we're under the limit
    final_bytes = glyph_count * phi_res * theta_res * bytes_per_sample
    if final_bytes > max_buffer_bytes:
        # Emergency reduction: calculate exact size that fits
        max_samples = max_buffer_bytes // (glyph_count * bytes_per_sample)
        # Find balanced phi/theta split (aim for 2:1 ratio)
        theta_res = int(np.sqrt(max_samples / 2))
        phi_res = max_samples // theta_res
    
    # Round to even counts to keep indexing simple
    if phi_res % 2:
        phi_res += 1
    if theta_res % 2:
        theta_res += 1

    return (int(phi_res), int(theta_res))


def _create_optimized_sh_billboard(
    coeffs,
    *,
    centers=None,
    sphere=None,
    basis_type="standard",
    color_type="sign",
    l_max=None,
    scale=1.0,
    shininess=50,
    opacity=None,
    enable_picking=True,
    use_precomputation=True,
    tight_fit=True,
    use_bicubic=False,
):
    """Create optimized SH billboard with precomputation and caching.
    
    This function creates spherical harmonics billboard actors with
    optimization techniques including:
    - Precomputed lookup tables for faster evaluation
    - Coefficient caching to avoid redundant computations
    - Configurable level-of-detail based on requirements
    - Efficient memory management and data structures
    """
    
    coeffs_arr = np.asarray(coeffs, dtype=np.float32)
    if coeffs_arr.ndim == 4:
        n_coeff = coeffs_arr.shape[-1]
    elif coeffs_arr.ndim == 2:
        n_coeff = coeffs_arr.shape[1]
    else:
        raise ValueError("coeffs must be (X,Y,Z,N) array")
    
    inferred_l_max = get_lmax(n_coeff, basis_type=basis_type)
    effective_l_max = l_max if l_max is not None else inferred_l_max
    
    # Cache key for precomputed data
    cache_key = (effective_l_max, basis_type, 128, 64, use_precomputation)
    
    if cache_key in _SH_PRECOMPUTE_CACHE:
        precompute_data = _SH_PRECOMPUTE_CACHE[cache_key]
    else:
        precompute_data = _generate_precompute_data(effective_l_max, basis_type)
        _SH_PRECOMPUTE_CACHE[cache_key] = precompute_data
    
    # Create the base actor using standard pipeline
    actor = sph_glyph_billboard(
        coeffs,
        centers=centers,
        sphere=sphere,
        basis_type=basis_type,
        color_type=color_type,
        l_max=l_max,
        scale=scale,
        shininess=shininess,
        opacity=opacity,
        enable_picking=enable_picking,
        use_precomputation=False,
        tight_fit=tight_fit,
    )
    
    # Attach advanced optimization data
    actor._precompute_data = precompute_data
    actor._is_precomputed = True
    actor._is_optimized = use_precomputation
    actor._cache_key = cache_key
    actor._optimization_level = "optimized" if use_precomputation else "standard"

    # Add optimization parameters
    actor._use_fast_approximation = effective_l_max <= 12  # Use analytical for low orders
    actor._use_level_of_detail = True  # Enable LOD
    actor._use_early_discard = True   # Enable early culling
    actor._distance_field_resolution = precompute_data.get('distance_field', np.array([])).shape
    actor._sh_use_bicubic = use_bicubic  # Enable bicubic interpolation (16 samples vs 4)

    if use_precomputation:
        _attach_precomputed_radius_tables(actor, precompute_data)

    return actor


def _attach_precomputed_radius_tables(actor, precompute_data):
    """Attach per-glyph spherical lookup tables to an optimized actor."""

    if not hasattr(actor, "sh_coeffs") or getattr(actor, "coeffs_per_glyph", 0) <= 0:
        return

    resolution = precompute_data.get("resolution", (0, 0))
    if len(resolution) != 2:
        return

    n_coeffs = int(actor.coeffs_per_glyph)
    glyph_count = int(getattr(actor, "billboard_count", 0))
    if glyph_count <= 0:
        return

    if glyph_count > _MAX_GPU_LUT_GLYPHS:
        actor._sh_use_radius_lut = False
        actor._sh_radius_lut_buffer = None
        actor._sh_normal_lut_buffer = None
        actor._is_optimized = False
        actor._sh_lut_ready = True
        return

    phi_res, theta_res = _select_lut_resolution(
        getattr(actor, "_l_max", precompute_data.get("l_max", 0)),
        glyph_count,
        resolution,
    )

    if theta_res <= 0 or phi_res <= 0:
        return

    sample_count = theta_res * phi_res
    total_samples = glyph_count * sample_count

    # Check buffer size limits (WebGPU max: 268MB)
    radius_buffer_size_mb = (total_samples * 4) / (1024 ** 2)  # float32 = 4 bytes
    normal_buffer_size_mb = (total_samples * 4 * 4) / (1024 ** 2)  # vec4<f32> = 16 bytes
    total_buffer_size_mb = radius_buffer_size_mb + normal_buffer_size_mb
    max_buffer_size_mb = 256
    
    skip_normal_lut = False
    if total_buffer_size_mb > max_buffer_size_mb * 0.9:
        if radius_buffer_size_mb < max_buffer_size_mb * 0.9:
            skip_normal_lut = True
        else:
            actor._sh_use_radius_lut = False
            actor._sh_radius_lut_buffer = None
            actor._sh_normal_lut_buffer = None
            actor._sh_lut_ready = True
            return

    usage = (
        wgpu.BufferUsage.STORAGE
        | wgpu.BufferUsage.COPY_SRC
        | wgpu.BufferUsage.COPY_DST
    )

    radius_lut = np.zeros(total_samples, dtype=np.float32)

    actor._sh_lut_theta_res = theta_res
    actor._sh_lut_phi_res = phi_res
    actor._sh_lut_stride = sample_count
    actor._sh_theta_step = np.pi / max(theta_res - 1, 1)
    actor._sh_phi_step = (2.0 * np.pi) / max(phi_res, 1)

    actor._sh_radius_lut_buffer = Buffer(radius_lut, usage=usage)
    
    if skip_normal_lut:
        dummy_normal = np.zeros((1, 4), dtype=np.float32)
        actor._sh_normal_lut_buffer = Buffer(dummy_normal, usage=usage)
        actor._sh_skip_normal_lut = True
    else:
        normal_lut = np.zeros((total_samples, 4), dtype=np.float32)
        actor._sh_normal_lut_buffer = Buffer(normal_lut, usage=usage)
        actor._sh_skip_normal_lut = False
    
    actor._sh_use_radius_lut = True
    actor._sh_lut_ready = False
    actor._sh_lut_needs_dispatch = True
    
    try:
        l_max = getattr(actor, "_l_max", 4)
        _populate_radius_lut_gpu_analytical(
            actor, phi_res, theta_res, glyph_count, n_coeffs, l_max
        )
        actor._sh_lut_ready = True
        actor._sh_lut_needs_dispatch = False
    except Exception:
        pass


def _populate_radius_lut_cpu(actor, phi_res, theta_res, glyph_count, n_coeffs):
    """Populate radius LUT on CPU by evaluating SH at sampled directions."""
    coeffs_buffer = actor.sh_coeffs
    if coeffs_buffer is None or not hasattr(coeffs_buffer, 'data'):
        return
    
    coeffs = coeffs_buffer.data
    
    if not isinstance(coeffs, np.ndarray):
        coeffs = np.asarray(coeffs, dtype=np.float32)
    
    if coeffs.ndim == 1:
        expected_size = glyph_count * n_coeffs
        if coeffs.shape[0] != expected_size:
            return
        coeffs = coeffs.reshape(glyph_count, n_coeffs)
    elif coeffs.shape[0] != glyph_count or coeffs.shape[1] != n_coeffs:
        return
    
    radius_lut = actor._sh_radius_lut_buffer.data
    
    if not isinstance(radius_lut, np.ndarray):
        radius_lut = np.asarray(radius_lut, dtype=np.float32)
    
    theta_vals = (np.arange(theta_res) + 0.5) * (np.pi / theta_res)
    phi_vals = (np.arange(phi_res) + 0.5) * (2.0 * np.pi / phi_res)
    
    phi_grid, theta_grid = np.meshgrid(phi_vals, theta_vals, indexing='xy')
    
    sin_theta = np.sin(theta_grid)
    x_dirs = sin_theta * np.cos(phi_grid)  # Shape: (theta_res, phi_res)
    y_dirs = sin_theta * np.sin(phi_grid)
    z_dirs = np.cos(theta_grid)
    
    # Stack into (theta_res * phi_res, 3) array of directions
    n_dirs = theta_res * phi_res
    directions = np.stack([
        x_dirs.ravel(),
        y_dirs.ravel(),
        z_dirs.ravel()
    ], axis=1)  # Shape: (n_dirs, 3)
    
    # Get L_max from number of coefficients
    l_max = get_lmax(n_coeffs)
    
    # Compute SH basis matrix for all directions at once
    # This is much faster than calling it millions of times!
    basis_matrix = create_sh_basis_matrix(directions, l_max)
    
    for glyph_id in range(glyph_count):
        glyph_radii = basis_matrix @ coeffs[glyph_id]
        glyph_radii = np.maximum(0.0, glyph_radii)
        
        start_idx = glyph_id * n_dirs
        end_idx = start_idx + n_dirs
        radius_lut[start_idx:end_idx] = glyph_radii
    
    actor._sh_radius_lut_buffer.update_full()


def _populate_radius_lut_gpu_nn(actor, phi_res, theta_res, glyph_count, n_coeffs):
    """Populate radius LUT using GPU neural network (L_max=4 only)."""
    import json
    import time
    
    # Get SH coefficients from actor
    coeffs_buffer = actor.sh_coeffs
    if coeffs_buffer is None or not hasattr(coeffs_buffer, 'data'):
        raise RuntimeError("No sh_coeffs buffer found")
    
    coeffs = coeffs_buffer.data
    if not isinstance(coeffs, np.ndarray):
        coeffs = np.asarray(coeffs, dtype=np.float32)
    
    if coeffs.ndim == 1:
        coeffs = coeffs.reshape(glyph_count, n_coeffs)
    
    # Get WebGPU device - need to get it from the window context
    # For now, create a new device
    adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
    device = adapter.request_device_sync()
    
    # Load trained neural network weights
    nn_weights_path = (
        "/home/moabouag/dev/fury/fury/wgsl/sh_lookup_standard_h64_lmax_4.json"
    )
    with open(nn_weights_path) as f:
        data = json.load(f)
    
    config = data['config']
    layers = data['layers']
    
    # Flatten weights for GPU
    layer1_weight = np.array(layers[0]['W'], dtype=np.float32).flatten()
    layer1_bias = np.array(layers[0]['b'], dtype=np.float32)
    layer2_weight = np.array(layers[1]['W'], dtype=np.float32).flatten()
    layer2_bias = np.array(layers[1]['b'], dtype=np.float32)
    layer3_weight = np.array(layers[2]['W'], dtype=np.float32).flatten()
    layer3_bias = np.array(layers[2]['b'], dtype=np.float32)
    
    start_time = time.perf_counter()
    
    # Create GPU buffers for neural network weights
    coeffs_gpu = device.create_buffer_with_data(
        data=coeffs.tobytes(),
        usage=wgpu.BufferUsage.STORAGE,
    )
    
    lut_size = glyph_count * phi_res * theta_res
    lut_gpu = device.create_buffer(
        size=lut_size * 4,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC,
    )
    
    layer1_w_buf = device.create_buffer_with_data(
        data=layer1_weight.tobytes(), usage=wgpu.BufferUsage.STORAGE
    )
    layer1_b_buf = device.create_buffer_with_data(
        data=layer1_bias.tobytes(), usage=wgpu.BufferUsage.STORAGE
    )
    layer2_w_buf = device.create_buffer_with_data(
        data=layer2_weight.tobytes(), usage=wgpu.BufferUsage.STORAGE
    )
    layer2_b_buf = device.create_buffer_with_data(
        data=layer2_bias.tobytes(), usage=wgpu.BufferUsage.STORAGE
    )
    layer3_w_buf = device.create_buffer_with_data(
        data=layer3_weight.tobytes(), usage=wgpu.BufferUsage.STORAGE
    )
    layer3_b_buf = device.create_buffer_with_data(
        data=layer3_bias.tobytes(), usage=wgpu.BufferUsage.STORAGE
    )
    
    # Uniforms
    uniforms_data = np.array([
        glyph_count, n_coeffs, phi_res, theta_res,
        config['hidden_size'], 32, 0, 0
    ], dtype=np.uint32)
    uniforms_buf = device.create_buffer_with_data(
        data=uniforms_data.tobytes(), usage=wgpu.BufferUsage.UNIFORM
    )
    
    # Load compute shader
    shader_path = (
        "/home/moabouag/dev/fury/fury/wgsl/sh_nn_lut_populate.wgsl"
    )
    with open(shader_path) as f:
        shader_code = f.read()
    
    shader_module = device.create_shader_module(code=shader_code)
    
    # Create bind group layout
    bgl = device.create_bind_group_layout(entries=[
        {"binding": i, "visibility": wgpu.ShaderStage.COMPUTE,
         "buffer": {"type": t}}
        for i, t in enumerate([
            wgpu.BufferBindingType.read_only_storage,  # 0: coeffs
            wgpu.BufferBindingType.storage,            # 1: lut
            wgpu.BufferBindingType.read_only_storage,  # 2: layer1_w
            wgpu.BufferBindingType.read_only_storage,  # 3: layer1_b
            wgpu.BufferBindingType.read_only_storage,  # 4: layer2_w
            wgpu.BufferBindingType.read_only_storage,  # 5: layer2_b
            wgpu.BufferBindingType.read_only_storage,  # 6: layer3_w
            wgpu.BufferBindingType.read_only_storage,  # 7: layer3_b
            wgpu.BufferBindingType.uniform,            # 8: uniforms
        ])
    ])
    
    # Create bind group
    bg = device.create_bind_group(layout=bgl, entries=[
        {"binding": i, "resource": {"buffer": b, "offset": 0, "size": b.size}}
        for i, b in enumerate([
            coeffs_gpu, lut_gpu,
            layer1_w_buf, layer1_b_buf,
            layer2_w_buf, layer2_b_buf,
            layer3_w_buf, layer3_b_buf,
            uniforms_buf
        ])
    ])
    
    # Create pipeline
    pipeline_layout = device.create_pipeline_layout(bind_group_layouts=[bgl])
    pipeline = device.create_compute_pipeline(
        layout=pipeline_layout,
        compute={"module": shader_module, "entry_point": "compute_lut"},
    )
    
    # Dispatch compute shader
    workgroups_x = glyph_count
    workgroups_y = (theta_res + 7) // 8
    workgroups_z = (phi_res + 7) // 8
    
    command_encoder = device.create_command_encoder()
    compute_pass = command_encoder.begin_compute_pass()
    compute_pass.set_pipeline(pipeline)
    compute_pass.set_bind_group(0, bg)
    compute_pass.dispatch_workgroups(workgroups_x, workgroups_y, workgroups_z)
    compute_pass.end()
    device.queue.submit([command_encoder.finish()])
    device.queue.on_submitted_work_done_sync()
    
    compute_time = time.perf_counter() - start_time
    
    # Copy results back to actor's LUT buffer
    readback_buf = device.create_buffer(
        size=lut_gpu.size,
        usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ,
    )
    
    cmd = device.create_command_encoder()
    cmd.copy_buffer_to_buffer(lut_gpu, 0, readback_buf, 0, lut_gpu.size)
    device.queue.submit([cmd.finish()])
    device.queue.on_submitted_work_done_sync()
    
    readback_buf.map_sync(mode=wgpu.MapMode.READ)
    lut_data = np.frombuffer(readback_buf.read_mapped(), dtype=np.float32).copy()
    readback_buf.unmap()
    
    # Update actor's LUT buffer
    radius_lut = actor._sh_radius_lut_buffer.data
    if not isinstance(radius_lut, np.ndarray):
        radius_lut = np.asarray(radius_lut, dtype=np.float32)
    radius_lut[:] = lut_data
    actor._sh_radius_lut_buffer.update_full()


def _populate_radius_lut_gpu_analytical(
    actor, phi_res, theta_res, glyph_count, n_coeffs, l_max
):
    """Populate radius LUT using GPU analytical SH evaluation."""
    import time
    
    # Get SH coefficients from actor
    coeffs_buffer = actor.sh_coeffs
    if coeffs_buffer is None or not hasattr(coeffs_buffer, 'data'):
        raise RuntimeError("No sh_coeffs buffer found")
    
    coeffs = coeffs_buffer.data
    if not isinstance(coeffs, np.ndarray):
        coeffs = np.asarray(coeffs, dtype=np.float32)
    
    if coeffs.ndim == 1:
        coeffs = coeffs.reshape(glyph_count, n_coeffs)
    
    # Get WebGPU device
    adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
    device = adapter.request_device_sync()
    
    # Get device buffer limit (cached after first call)
    max_buffer_bytes = _get_gpu_max_buffer_size()
    
    # Calculate chunk size based on actual device buffer limit
    lut_samples_per_glyph = phi_res * theta_res
    bytes_per_sample = 4  # float32
    
    # Reserve space for coeffs buffer and overhead (use 40% of max for LUT buffer)
    safe_buffer_bytes = int(max_buffer_bytes * 0.4)
    max_glyphs_per_chunk = safe_buffer_bytes // (lut_samples_per_glyph * bytes_per_sample)
    max_glyphs_per_chunk = max(1, max_glyphs_per_chunk)
    
    if glyph_count <= max_glyphs_per_chunk:
        # Single chunk - process all at once
        _populate_radius_lut_gpu_analytical_chunk(
            actor, phi_res, theta_res, glyph_count, n_coeffs, l_max,
            coeffs, 0, glyph_count
        )
    else:
        for chunk_start in range(0, glyph_count, max_glyphs_per_chunk):
            chunk_end = min(chunk_start + max_glyphs_per_chunk, glyph_count)
            
            _populate_radius_lut_gpu_analytical_chunk(
                actor, phi_res, theta_res, glyph_count, n_coeffs, l_max,
                coeffs, chunk_start, chunk_end
            )


def _populate_radius_lut_gpu_analytical_chunk(
    actor, phi_res, theta_res, total_glyph_count, n_coeffs, l_max,
    all_coeffs, chunk_start, chunk_end
):
    """Process a single chunk of glyphs for GPU analytical LUT population."""
    import time
    
    chunk_size = chunk_end - chunk_start
    coeffs_chunk = all_coeffs[chunk_start:chunk_end]
    
    adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
    device = adapter.request_device_sync()
    
    start_time = time.perf_counter()
    
    lut_size = chunk_size * phi_res * theta_res
    
    coeffs_gpu = device.create_buffer_with_data(
        data=coeffs_chunk.tobytes(),
        usage=wgpu.BufferUsage.STORAGE,
    )
    
    lut_gpu = device.create_buffer(
        size=lut_size * 4,
        usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_SRC,
    )
    
    # Uniforms - note: using chunk_size for computation
    uniforms_data = np.array([
        chunk_size, n_coeffs, phi_res, theta_res,
        l_max, 0, 0, 0
    ], dtype=np.uint32)
    uniforms_buf = device.create_buffer_with_data(
        data=uniforms_data.tobytes(), usage=wgpu.BufferUsage.UNIFORM
    )
    
    # Load analytical compute shader
    from pathlib import Path
    shader_path = Path(__file__).parent.parent / "wgsl" / "sh_analytical_lut_populate.wgsl"
    with open(shader_path) as f:
        shader_code = f.read()
    
    shader_module = device.create_shader_module(code=shader_code)
    
    # Create bind group layout
    bgl = device.create_bind_group_layout(entries=[
        {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE,
         "buffer": {"type": wgpu.BufferBindingType.read_only_storage}},
        {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE,
         "buffer": {"type": wgpu.BufferBindingType.storage}},
        {"binding": 2, "visibility": wgpu.ShaderStage.COMPUTE,
         "buffer": {"type": wgpu.BufferBindingType.uniform}},
    ])
    
    # Create bind group
    bg = device.create_bind_group(layout=bgl, entries=[
        {"binding": 0, "resource": {"buffer": coeffs_gpu, "offset": 0, "size": coeffs_gpu.size}},
        {"binding": 1, "resource": {"buffer": lut_gpu, "offset": 0, "size": lut_gpu.size}},
        {"binding": 2, "resource": {"buffer": uniforms_buf, "offset": 0, "size": uniforms_buf.size}},
    ])
    
    # Create pipeline
    pipeline_layout = device.create_pipeline_layout(bind_group_layouts=[bgl])
    pipeline = device.create_compute_pipeline(
        layout=pipeline_layout,
        compute={"module": shader_module, "entry_point": "compute_lut"},
    )
    
    # Dispatch compute shader
    workgroups_x = chunk_size
    workgroups_y = (theta_res + 7) // 8
    workgroups_z = (phi_res + 7) // 8
    
    command_encoder = device.create_command_encoder()
    compute_pass = command_encoder.begin_compute_pass()
    compute_pass.set_pipeline(pipeline)
    compute_pass.set_bind_group(0, bg)
    compute_pass.dispatch_workgroups(workgroups_x, workgroups_y, workgroups_z)
    compute_pass.end()
    device.queue.submit([command_encoder.finish()])
    device.queue.on_submitted_work_done_sync()
    
    compute_time = time.perf_counter() - start_time
    
    # Copy results back to actor's LUT buffer
    readback_buf = device.create_buffer(
        size=lut_gpu.size,
        usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ,
    )
    
    cmd = device.create_command_encoder()
    cmd.copy_buffer_to_buffer(lut_gpu, 0, readback_buf, 0, lut_gpu.size)
    device.queue.submit([cmd.finish()])
    device.queue.on_submitted_work_done_sync()
    
    readback_buf.map_sync(mode=wgpu.MapMode.READ)
    lut_data = np.frombuffer(readback_buf.read_mapped(), dtype=np.float32).copy()
    readback_buf.unmap()
    
    # Update actor's LUT buffer at the correct offset for this chunk
    radius_lut = actor._sh_radius_lut_buffer.data
    if not isinstance(radius_lut, np.ndarray):
        radius_lut = np.asarray(radius_lut, dtype=np.float32)
    
    # Calculate offset in the full LUT buffer
    samples_per_glyph = phi_res * theta_res
    offset_start = chunk_start * samples_per_glyph
    offset_end = chunk_end * samples_per_glyph
    
    radius_lut[offset_start:offset_end] = lut_data
    actor._sh_radius_lut_buffer.update_range(offset_start * 4, len(lut_data) * 4)


def _evaluate_sh_at_direction(coeffs, x, y, z):
    """Evaluate spherical harmonics at a direction (x,y,z)."""
    direction = np.array([[x, y, z]], dtype=np.float32)
    
    # Get the SH basis matrix for this direction
    l_max = get_lmax(len(coeffs))
    basis_matrix = create_sh_basis_matrix(direction, l_max)
    
    # Dot product: basis_matrix is (1, n_coeffs), coeffs is (n_coeffs,)
    radius = np.dot(basis_matrix[0], coeffs)
    
    return float(radius)


def _generate_precompute_data(l_max, basis_type="standard"):
    """Generate lookup-table metadata for optimized SH billboards."""

    cache_key = f"precompute_{l_max}_{basis_type}"
    if cache_key in _SH_PRECOMPUTE_CACHE:
        return _SH_PRECOMPUTE_CACHE[cache_key]

    if l_max >= 8:
        resolution = (128, 64)  # Reduced to fit in 256 MB GPU limit
    elif l_max >= 4:
        resolution = (96, 48)
    else:
        resolution = (64, 32)

    precompute_data = {
        "resolution": resolution,
        "l_max": l_max,
        "basis_type": basis_type,
    }

    _SH_PRECOMPUTE_CACHE[cache_key] = precompute_data
    return precompute_data


def _generate_lod_data(basis_matrix, l_max, n_coeffs):
    """Generate multi-resolution data for level-of-detail rendering."""
    
    lod_levels = [
        n_coeffs,           # Full resolution
        max(n_coeffs // 2, 1),  # Half resolution  
        max(n_coeffs // 4, 1),  # Quarter resolution
        1                   # Just the base term
    ]
    
    lod_data = {}
    for i, level_coeffs in enumerate(lod_levels):
        # Truncate basis matrix to this LOD level
        lod_basis = basis_matrix[:, :level_coeffs].copy()
        lod_data[f'lod_{i}'] = {
            'basis_matrix': lod_basis.flatten().astype(np.float32),
            'n_coeffs': level_coeffs,
            'quality_factor': level_coeffs / n_coeffs
        }
    
    return lod_data


def get_sh_cache_info():
    """Get information about the global SH precompute cache.
    
    Returns
    -------
    dict
        Cache statistics including number of configurations and memory usage.
    """
    total_memory = sum(len(data) * 4 for data in _SH_PRECOMPUTE_CACHE.values())  # 4 bytes per float32
    
    return {
        'num_cached_configs': len(_SH_PRECOMPUTE_CACHE),
        'total_memory_kb': total_memory / 1024,
        'configurations': [
            {
                'l_max': key[0],
                'basis_type': key[1],
                'phi_resolution': key[2],
                'theta_resolution': key[3],
                'memory_kb': len(_SH_PRECOMPUTE_CACHE[key]) * 4 / 1024
            }
            for key in _SH_PRECOMPUTE_CACHE.keys()
        ]
    }


def clear_sh_cache():
    """Clear the global SH precompute cache."""
    global _SH_PRECOMPUTE_CACHE
    num_cleared = len(_SH_PRECOMPUTE_CACHE)
    _SH_PRECOMPUTE_CACHE.clear()
    return num_cleared


def _create_billboard_actor(
    centers,
    colors,
    sizes,
    opacity,
    enable_picking,
    *,
    material_cls,
    material_kwargs=None,
    actor_cls=None,
):
    """Build a ``Billboard`` instance from broadcasted inputs.

    Parameters
    ----------
    centers : array_like
        Position of each billboard specified as an ``(N, 3)`` array or
        broadcastable equivalent.
    colors : array_like
        RGB or RGBA color per billboard. A single color is broadcast when
        needed.
    sizes : array_like
        Width and height per billboard. Accepts scalar, ``(2,)`` pair,
        ``(N,)`` radius (interpreted as square billboards), or ``(N, 2)`` data.
    opacity : float or None
        Global opacity multiplier. ``None`` keeps the material default.
    enable_picking : bool
        Whether the billboard should write picking information.
    material_cls : type[BillboardMaterial]
        Material class used to instantiate the billboard actor.
    material_kwargs : dict, optional
        Additional keyword arguments forwarded to ``material_cls``.

    Returns
    -------
    Billboard
        Configured billboard world object containing geometry, material and
        metadata about the generated billboards.
    """

    centers = np.asarray(centers, dtype=np.float32)
    if centers.ndim == 1:
        centers = centers.reshape(1, 3)
    n = len(centers)

    colors = np.asarray(colors, dtype=np.float32)
    if colors.ndim == 1:
        colors = np.tile(colors, (n, 1))
    elif colors.shape[0] != n:
        colors = np.tile(colors[0], (n, 1))

    sizes = np.asarray(sizes, dtype=np.float32)
    if sizes.ndim == 0:
        sizes = np.full((n, 2), float(sizes))
    elif sizes.ndim == 1:
        if sizes.size == 2:
            sizes = np.tile(sizes, (n, 1))
        elif sizes.size == n:
            sizes = np.column_stack([sizes, sizes])
        else:
            sizes = np.full((n, 2), sizes.flat[0])
    elif sizes.shape[0] != n:
        sizes = np.tile(sizes[0], (n, 1))

    opacity = validate_opacity(opacity)

    repeats = 6  # 2 triangles per quad
    pos = np.repeat(centers, repeats, axis=0).astype(np.float32)
    col = np.repeat(colors, repeats, axis=0).astype(np.float32)
    indices = np.arange(pos.shape[0], dtype=np.uint32)

    # Encode per-billboard size in normals so shaders can fetch dimensions
    normals = np.repeat(
        np.column_stack([sizes, np.ones((n, 1), dtype=np.float32)]),
        repeats,
        axis=0,
    ).astype(np.float32)

    geometry = buffer_to_geometry(
        positions=pos,
        colors=col,
        normals=normals,
        indices=indices,
    )

    material_kwargs = material_kwargs or {}
    material = material_cls(
        pick_write=enable_picking,
        opacity=opacity,
        color_mode="vertex",
        **material_kwargs,
    )

    actor_type = Billboard if actor_cls is None else actor_cls
    obj = actor_type(geometry=geometry, material=material)
    obj.billboard_count = n
    obj.billboard_centers = centers.copy()
    obj.billboard_sizes = sizes.copy()
    return obj


class Billboard(Mesh):
    """World object representing one or more billboards.

    Geometry buffers are duplicated per 6 vertices (two triangles) per
    billboard; vertex shader reconstructs quad via vertex_index math and
    uses camera right/up vectors to orient. Size metadata is stored on
    ``billboard_sizes`` and reused by shaders for impostor variants.
    """

    pass


class SphGlyphBillboard(Billboard):
    """Billboard world object specialised for spherical harmonic glyph impostors."""

    _basis_type = "standard"

    @property
    def l_max(self):
        """Maximum spherical harmonic degree currently used for rendering."""

        return getattr(self, "_l_max", -1)

    @l_max.setter
    def l_max(self, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError("The attribute 'l_max' must be a non-negative integer.")

        max_supported = get_lmax(getattr(self, "n_coeff", 0), basis_type=self._basis_type)
        if value > max_supported:
            raise ValueError(
                "The provided 'l_max' exceeds the number of spherical harmonic coefficients."
            )

        self._l_max = value
        n_coeffs = get_n_coeffs(value, basis_type=self._basis_type)
        self.material.n_coeffs = n_coeffs


def billboard(
    centers,
    *,
    colors=(1, 1, 1),
    sizes=(1, 1),
    opacity=None,
    enable_picking=True,
):
    """Create a billboard world object.

    Parameters
    ----------
    centers : (N,3) array_like
        Billboard positions.
    colors : (N,3|4) array_like or single color
        Per-billboard RGB(A) colors.
    sizes : (N,2) | (2,) | float | (N,) array_like
        Width/height per billboard. Scalar or single pair broadcast.
    opacity : float, optional
        Global opacity multiplier (0..1).
    enable_picking : bool
        Whether billboard is pickable.

    Returns
    -------
    Billboard
        Billboard world object configured with the provided geometry and
        material.
    """
    return _create_billboard_actor(
        centers,
        colors,
        sizes,
        opacity,
        enable_picking,
        material_cls=BillboardMaterial,
    )


def create_billboard_sphere(
    centers,
    *,
    colors=(1, 1, 1),
    radii=0.5,
    opacity=None,
    enable_picking=True,
):
    """Create a billboard impostor sphere world object.

    Parameters
    ----------
    centers : array_like
        Sphere centers provided as an ``(N, 3)`` array or broadcastable input.
    colors : array_like, optional
        RGB or RGBA color per sphere. Single color inputs are broadcast.
    radii : array_like, optional
        Scalar radii or per-sphere radii array. Used to compute billboard size.
    opacity : float, optional
        Opacity multiplier applied to the material.
    enable_picking : bool, optional
        Whether the impostor spheres support picking.

    Returns
    -------
    Billboard
        Billboard actor configured to simulate spheres using impostor quads.
    """

    sizes = np.asarray(radii, dtype=np.float32) * 2.0
    obj = _create_billboard_actor(
        centers,
        colors,
        sizes,
        opacity,
        enable_picking,
        material_cls=BillboardSphereMaterial,
    )
    obj.billboard_radii = obj.billboard_sizes[:, 0] * 0.5
    obj.billboard_mode = "impostor"
    return obj


def sph_glyph_billboard(
    coeffs,
    *,
    centers=None,
    sphere=None,
    basis_type="standard",
    color_type="sign",
    l_max=None,
    scale=1.0,
    shininess=50,
    opacity=None,
    enable_picking=True,
    use_precomputation=True,
    tight_fit=True,
    use_bicubic=False,
):
    """Create spherical harmonic glyph impostors rendered as billboards.

    Parameters
    ----------
    coeffs : ndarray
        Spherical harmonics coefficients arranged either as ``(X, Y, Z, N)`` grid
        or flattened ``(M, N)`` array where ``N`` is the number of coefficients.
    centers : ndarray, optional
        Glyph centers provided as ``(M, 3)`` array. Required when ``coeffs`` is
        two-dimensional. When omitted and ``coeffs`` is four-dimensional, grid
        indices are used as centers.
    sphere : {str, tuple}, optional
        Sphere primitive used to estimate glyph extent.
    basis_type : {'standard', 'descoteaux07'}, optional
        Harmonic basis of the supplied coefficients.
    color_type : {'sign', 'orientation'}, optional
        Color mapping applied in the fragment shader.
    l_max : int, optional
        Maximum harmonic degree to evaluate.
    scale : float, optional
        Global scale applied to each glyph radius.
    shininess : float, optional
        Specular shininess forwarded to the underlying Phong material.
    opacity : float, optional
        Global opacity multiplier.
    enable_picking : bool, optional
        Whether glyphs should contribute to picking buffers.
    use_precomputation : bool, optional
        Whether to use precomputed lookup tables for faster rendering.
    tight_fit : bool, optional
        If True, use minimal padding (2%) for tighter billboard fit and better
        performance. If False, use 10% padding for safer margins. Default True.

    Returns
    -------
    SphGlyphBillboard
        Billboard actor with spherical harmonic glyphs.
    """
    
    if use_precomputation:
        return _create_optimized_sh_billboard(
            coeffs,
            centers=centers,
            sphere=sphere,
            basis_type=basis_type,
            color_type=color_type,
            l_max=l_max,
            scale=scale,
            shininess=shininess,
            opacity=opacity,
            enable_picking=enable_picking,
            tight_fit=tight_fit,
            use_bicubic=use_bicubic,
        )

    coeffs_arr = np.asarray(coeffs, dtype=np.float32)

    if coeffs_arr.ndim == 4:
        data_shape = coeffs_arr.shape[:3]
        coeffs_flat = coeffs_arr.reshape(-1, coeffs_arr.shape[-1])
        if centers is None:
            grid = np.indices(data_shape, dtype=np.float32).reshape(3, -1).T
            centers_arr = grid
        else:
            centers_arr = np.asarray(centers, dtype=np.float32)
            if centers_arr.shape[0] != coeffs_flat.shape[0]:
                raise ValueError(
                    "centers must match the number of glyphs implied by coeffs."
                )
    elif coeffs_arr.ndim == 2:
        if centers is None:
            raise ValueError(
                "centers must be provided when coeffs is a two-dimensional array."
            )
        centers_arr = np.asarray(centers, dtype=np.float32)
        coeffs_flat = coeffs_arr
        if centers_arr.shape[0] != coeffs_flat.shape[0]:
            raise ValueError("centers and coeffs must contain the same number of glyphs.")
        data_shape = None
    else:
        raise ValueError("coeffs must be a (X, Y, Z, N) or (M, N) array of SH coefficients.")

    if centers_arr.ndim != 2 or centers_arr.shape[1] != 3:
        raise ValueError("centers must be an array with shape (M, 3).")

    n_coeff = coeffs_flat.shape[1]
    if n_coeff < 1:
        raise ValueError("coeffs must contain at least one spherical harmonic coefficient.")

    if basis_type not in ("standard", "descoteaux07"):
        raise ValueError("basis_type must be one of 'standard' or 'descoteaux07'.")

    inferred_l_max = get_lmax(n_coeff, basis_type=basis_type)

    if l_max is None:
        material_n_coeffs = -1
    else:
        if not isinstance(l_max, int) or l_max < 0:
            raise ValueError("l_max must be a non-negative integer when provided.")
        if l_max > inferred_l_max:
            raise ValueError("l_max exceeds the degree supported by the provided coeffs.")
        material_n_coeffs = get_n_coeffs(l_max, basis_type=basis_type)

    if sphere is None:
        sphere = "symmetric362"

    if isinstance(sphere, str):
        sphere_vertices, _ = fp.prim_sphere(name=sphere)
    elif (
        isinstance(sphere, tuple)
        and len(sphere) == 2
        and all(isinstance(x, int) for x in sphere)
    ):
        sphere_vertices, _ = fp.prim_sphere(gen_faces=True, phi=sphere[0], theta=sphere[1])
    elif (
        isinstance(sphere, tuple)
        and len(sphere) == 2
        and isinstance(sphere[0], np.ndarray)
        and isinstance(sphere[1], np.ndarray)
    ):
        sphere_vertices, _ = sphere
    else:
        raise TypeError(
            "sphere must be a named primitive, a (phi, theta) tuple, or (vertices, faces)."
        )

    basis_matrix = create_sh_basis_matrix(sphere_vertices, inferred_l_max)
    if basis_matrix.shape[1] != n_coeff:
        raise ValueError(
            "Mismatch between coefficient count and generated spherical harmonic basis."
        )

    radii = coeffs_flat @ basis_matrix.T
    max_radius = np.max(np.abs(radii), axis=1)
    max_radius = np.where(max_radius > 1e-6, max_radius, np.full_like(max_radius, 1e-6))

    # Tight fit optimization: minimal padding for better performance
    # tight_fit=True:  1.02 = 2% safety margin (saves ~15% fragment shader cost)
    # tight_fit=False: 1.10 = 10% padding (safer but slower)
    padding = 1.02 if tight_fit else 1.10
    sizes = (max_radius * scale * 2.0 * padding).astype(np.float32)
    sizes = np.column_stack([sizes, sizes])

    colors = np.ones((coeffs_flat.shape[0], 3), dtype=np.float32)

    material_kwargs = {
        "flat_shading": False,
        "shininess": shininess,
        "n_coeffs": material_n_coeffs,
        "scale": float(scale),
    }

    obj = _create_billboard_actor(
        centers_arr,
        colors,
        sizes,
        opacity,
        enable_picking,
        material_cls=SphGlyphMaterial,
        material_kwargs=material_kwargs,
        actor_cls=SphGlyphBillboard,
    )

    obj.billboard_radii = max_radius * scale
    obj.billboard_mode = "spherical_harmonic"
    obj.n_coeff = n_coeff
    obj.sh_coeffs = coeffs_flat.reshape(-1).astype(np.float32)
    obj.sh_coeffs_buffer = Buffer(obj.sh_coeffs)
    obj.coeffs_per_glyph = n_coeff
    obj.color_type = 0 if color_type == "sign" else 1
    obj._basis_type = basis_type
    obj._l_max = inferred_l_max
    obj.material.n_coeffs = material_n_coeffs
    if data_shape is not None:
        obj.data_shape = data_shape

    return obj


@register_wgpu_render_function(Billboard, BillboardMaterial)
def register_billboard_render_function(wobject):
    """Build the render pipeline for ``Billboard`` instances.

    Parameters
    ----------
    wobject : Billboard
        Billboard world object to bind to the shader pipeline.

    Returns
    -------
    tuple
        Tuple containing the configured shader instance.
    """
    from fury.shader import BillboardShader

    return (BillboardShader(wobject),)


@register_wgpu_render_function(Billboard, BillboardSphereMaterial)
def register_billboard_sphere_render_function(wobject):
    """Register the pipeline for billboard-based sphere impostors.

    Parameters
    ----------
    wobject : Billboard
        Billboard world object representing impostor spheres.

    Returns
    -------
    tuple
        Tuple containing the configured
        :class:`~fury.shader.BillboardSphereShader`.
    """
    from fury.shader import BillboardSphereShader

    return (BillboardSphereShader(wobject),)


@register_wgpu_render_function(SphGlyphBillboard, SphGlyphMaterial)
def register_billboard_sph_glyph_render_function(wobject):
    """Register the render pipeline for spherical harmonic billboard impostors."""

    from fury.shader import (
        BillboardSphGlyphPrecomputeShader,
        BillboardSphGlyphShader,
    )

    shaders = []
    if getattr(wobject, "_sh_use_radius_lut", False):
        shaders.append(BillboardSphGlyphPrecomputeShader(wobject))
    shaders.append(BillboardSphGlyphShader(wobject))
    return tuple(shaders)
