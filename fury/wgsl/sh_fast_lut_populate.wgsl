// GPU Compute Shader for Fast SH LUT Population using Precomputed Basis
// Uses shared basis functions - 5-10× faster than computing per glyph!

@group(0) @binding(0) var<storage, read> s_sh_coeffs: array<f32>;
@group(0) @binding(1) var<storage, read_write> s_radius_lut: array<f32>;
@group(0) @binding(2) var<storage, read> s_basis_lut: array<f32>;  // Precomputed basis!

struct ComputeUniforms {
    n_glyphs: u32,
    n_coeffs: u32,
    phi_res: u32,
    theta_res: u32,
    l_max: u32,
    _pad1: u32,
    _pad2: u32,
    _pad3: u32,
}
@group(0) @binding(3) var<uniform> uniforms: ComputeUniforms;

// Fast evaluation using precomputed basis
// Just dot product: radius = sum(coeffs[i] * basis[i])
fn evaluate_sh_fast(coeff_offset: u32, direction_idx: u32, n_coeffs: u32) -> f32 {
    var sum = 0.0;
    
    let basis_offset = direction_idx * n_coeffs;
    
    // Simple dot product - super fast!
    for (var i = 0u; i < n_coeffs; i++) {
        let coeff = s_sh_coeffs[coeff_offset + i];
        let basis = s_basis_lut[basis_offset + i];
        sum += coeff * basis;
    }
    
    return sum;
}

@compute @workgroup_size(1, 8, 8)
fn compute_lut(
    @builtin(global_invocation_id) global_id: vec3<u32>,
) {
    let glyph_id = global_id.x;
    let theta_idx = global_id.y;
    let phi_idx = global_id.z;
    
    let n_glyphs = uniforms.n_glyphs;
    let phi_res = uniforms.phi_res;
    let theta_res = uniforms.theta_res;
    let n_coeffs = uniforms.n_coeffs;
    
    // Bounds check
    if (glyph_id >= n_glyphs || theta_idx >= theta_res || phi_idx >= phi_res) {
        return;
    }
    
    // Get coefficient offset for this glyph
    let coeffs_offset = glyph_id * n_coeffs;
    
    // Get direction index
    let direction_idx = theta_idx * phi_res + phi_idx;
    
    // Evaluate using precomputed basis (FAST!)
    let radius = evaluate_sh_fast(coeffs_offset, direction_idx, n_coeffs);
    
    // Store in LUT
    let lut_idx = glyph_id * (phi_res * theta_res) + theta_idx * phi_res + phi_idx;
    s_radius_lut[lut_idx] = radius;
}
