@group(0) @binding(0) var<storage, read> s_sh_coeffs: array<f32>;
@group(0) @binding(1) var<storage, read_write> s_radius_lut: array<f32>;
@group(0) @binding(2) var<storage, read> nn_layer1_weight: array<f32>;
@group(0) @binding(3) var<storage, read> nn_layer1_bias: array<f32>;
@group(0) @binding(4) var<storage, read> nn_layer2_weight: array<f32>;  
@group(0) @binding(5) var<storage, read> nn_layer2_bias: array<f32>;
@group(0) @binding(6) var<storage, read> nn_layer3_weight: array<f32>;
@group(0) @binding(7) var<storage, read> nn_layer3_bias: array<f32>;

struct ComputeUniforms {
    n_glyphs: u32,
    n_coeffs: u32,
    phi_res: u32,
    theta_res: u32,
    hidden1_size: u32,
    hidden2_size: u32,
    _pad1: u32,
    _pad2: u32,
}
@group(0) @binding(8) var<uniform> uniforms: ComputeUniforms;

fn relu(x: f32) -> f32 {
    return max(0.0, x);
}

fn evaluate_nn(direction: vec3<f32>, coeffs_offset: u32) -> f32 {
    let n_coeffs = uniforms.n_coeffs;
    let h1_size = uniforms.hidden1_size;
    let h2_size = uniforms.hidden2_size;
    
    var hidden1: array<f32, 64>;
    for (var i = 0u; i < h1_size; i++) {
        var sum = nn_layer1_bias[i];
        
        sum += direction.x * nn_layer1_weight[i * 28u + 0u];
        sum += direction.y * nn_layer1_weight[i * 28u + 1u];
        sum += direction.z * nn_layer1_weight[i * 28u + 2u];
        
        // SH coefficients (next 25 inputs)
        for (var j = 0u; j < n_coeffs; j++) {
            let coeff = s_sh_coeffs[coeffs_offset + j];
            sum += coeff * nn_layer1_weight[i * 28u + 3u + j];
        }
        
        hidden1[i] = relu(sum);
    }
    
    // Layer 2: Hidden1(64) → Hidden2(32) with ReLU
    var hidden2: array<f32, 32>;
    for (var i = 0u; i < h2_size; i++) {
        var sum = nn_layer2_bias[i];
        for (var j = 0u; j < h1_size; j++) {
            sum += hidden1[j] * nn_layer2_weight[i * h1_size + j];
        }
        hidden2[i] = relu(sum);
    }
    
    // Layer 3: Hidden2(32) → Output(1)
    var output = nn_layer3_bias[0];
    for (var i = 0u; i < h2_size; i++) {
        output += hidden2[i] * nn_layer3_weight[i];
    }
    
    return max(0.0, output);  // Clamp to positive
}

// Compute shader entry point
// Workgroup: (glyph_id, theta_id, phi_id)
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
    
    // Compute spherical coordinates (uniform sampling)
    let theta = (f32(theta_idx) + 0.5) * (3.14159265359 / f32(theta_res));
    let phi = (f32(phi_idx) + 0.5) * (2.0 * 3.14159265359 / f32(phi_res));
    
    // Convert to Cartesian direction
    let sin_theta = sin(theta);
    let direction = vec3<f32>(
        sin_theta * cos(phi),
        sin_theta * sin(phi),
        cos(theta)
    );
    
    // Get coefficient offset for this glyph
    let coeffs_offset = glyph_id * n_coeffs;
    
    // Evaluate neural network
    let radius = evaluate_nn(direction, coeffs_offset);
    
    // Store in LUT (row-major order: glyph, theta, phi)
    let lut_idx = glyph_id * (phi_res * theta_res) + theta_idx * phi_res + phi_idx;
    s_radius_lut[lut_idx] = radius;
}
