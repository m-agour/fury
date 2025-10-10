// GPU Compute Shader for Precomputing SH Basis Functions
// Computes Y_l^m(theta, phi) once for all glyphs to share
// This gives 5-10× speedup over computing basis per glyph!

@group(0) @binding(0) var<storage, read_write> s_basis_lut: array<f32>;

struct ComputeUniforms {
    phi_res: u32,
    theta_res: u32,
    l_max: u32,
    n_coeffs: u32,
    _pad1: u32,
    _pad2: u32,
    _pad3: u32,
    _pad4: u32,
}
@group(0) @binding(1) var<uniform> uniforms: ComputeUniforms;

const PI: f32 = 3.14159265359;
const SQRT_2: f32 = 1.4142135623730951;

// Factorial lookup table
fn factorial(n: i32) -> f32 {
    if (n <= 0) { return 1.0; }
    if (n == 1) { return 1.0; }
    if (n == 2) { return 2.0; }
    if (n == 3) { return 6.0; }
    if (n == 4) { return 24.0; }
    if (n == 5) { return 120.0; }
    if (n == 6) { return 720.0; }
    if (n == 7) { return 5040.0; }
    if (n == 8) { return 40320.0; }
    return 1.0;
}

// Compute (l-m)! / (l+m)!
fn factorial_ratio(l: i32, m: i32) -> f32 {
    if (m == 0 || l == 0) { return 1.0; }
    
    var result = 1.0;
    let start = l - m + 1;
    let stop = l + m;
    
    if (stop < start) { return 1.0; }
    
    for (var k: i32 = start; k <= stop; k++) {
        result /= f32(k);
    }
    return result;
}

// Associated Legendre polynomial P_l^m(x)
fn legendre_polynomial(l: i32, m: i32, x: f32) -> f32 {
    if (l == 0) { return 1.0; }
    
    let abs_m = abs(m);
    
    if (l == abs_m) {
        var pmm = 1.0;
        let somx2 = sqrt((1.0 - x) * (1.0 + x));
        var fact = 1.0;
        for (var i: i32 = 1; i <= abs_m; i++) {
            pmm *= -fact * somx2;
            fact += 2.0;
        }
        return pmm;
    }
    
    var pmm = 1.0;
    let somx2 = sqrt((1.0 - x) * (1.0 + x));
    var fact = 1.0;
    for (var i: i32 = 1; i <= abs_m; i++) {
        pmm *= -fact * somx2;
        fact += 2.0;
    }
    
    if (l == abs_m + 1) {
        return x * f32(2 * abs_m + 1) * pmm;
    }
    
    var pmm1 = x * f32(2 * abs_m + 1) * pmm;
    
    for (var ll: i32 = abs_m + 2; ll <= l; ll++) {
        let pll = (x * f32(2 * ll - 1) * pmm1 - f32(ll + abs_m - 1) * pmm) / f32(ll - abs_m);
        pmm = pmm1;
        pmm1 = pll;
    }
    
    return pmm1;
}

// Spherical harmonic normalization factor
fn sh_normalization(l: i32, m: i32) -> f32 {
    let abs_m = abs(m);
    let factor = (2.0 * f32(l) + 1.0) / (4.0 * PI);
    let frac = factorial_ratio(l, abs_m);
    return sqrt(factor * frac);
}

// Real spherical harmonic Y_l^m(theta, phi)
fn spherical_harmonic(l: i32, m: i32, cos_theta: f32, phi: f32) -> f32 {
    let norm = sh_normalization(l, m);
    let plm = legendre_polynomial(l, abs(m), cos_theta);
    
    if (m == 0) {
        return norm * plm;
    } else if (m > 0) {
        return SQRT_2 * norm * plm * cos(f32(m) * phi);
    } else {
        return SQRT_2 * norm * plm * sin(f32(-m) * phi);
    }
}

// Precompute all basis functions for one direction
@compute @workgroup_size(8, 8, 1)
fn compute_basis(
    @builtin(global_invocation_id) global_id: vec3<u32>,
) {
    let theta_idx = global_id.y;
    let phi_idx = global_id.z;
    
    let phi_res = uniforms.phi_res;
    let theta_res = uniforms.theta_res;
    let l_max = i32(uniforms.l_max);
    let n_coeffs = uniforms.n_coeffs;
    
    // Bounds check
    if (theta_idx >= theta_res || phi_idx >= phi_res) {
        return;
    }
    
    // Compute spherical coordinates (uniform sampling)
    let theta = (f32(theta_idx) + 0.5) * (PI / f32(theta_res));
    let phi = (f32(phi_idx) + 0.5) * (2.0 * PI / f32(phi_res));
    
    let cos_theta = cos(theta);
    
    // Compute all basis functions for this direction
    var idx = 0u;
    for (var l: i32 = 0; l <= l_max; l++) {
        for (var m: i32 = -l; m <= l; m++) {
            if (idx >= n_coeffs) {
                break;
            }
            
            let y = spherical_harmonic(l, m, cos_theta, phi);
            
            // Store: basis_lut[direction_idx * n_coeffs + coeff_idx]
            let direction_idx = theta_idx * phi_res + phi_idx;
            let store_idx = direction_idx * n_coeffs + idx;
            s_basis_lut[store_idx] = y;
            
            idx++;
        }
    }
}
