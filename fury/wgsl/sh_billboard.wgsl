{$ include 'pygfx.std.wgsl' $}
{$ include 'pygfx.light_phong.wgsl' $}

const NUM_COEFFS = i32({{ n_coeffs }});
const L_MAX = i32({{ l_max }});
const COLOR_TYPE = i32({{ color_type }});
const SH_STRIDE: u32 = u32(L_MAX + 1);
const SH_TABLE_SIZE: u32 = SH_STRIDE * u32(L_MAX + 1);
const SH_TRIG_SIZE: u32 = u32(L_MAX + 1);

const USE_PRECOMPUTED_RADIUS_LUT = bool({{ use_precomputed_radius_lut }});
const USE_BICUBIC_INTERPOLATION = bool({{ use_bicubic_interpolation }});
const LUT_THETA_RES = u32({{ radius_lut_theta }});
const LUT_PHI_RES = u32({{ radius_lut_phi }});
const LUT_STRIDE = u32({{ radius_lut_stride }});

struct VertexInput {
    @builtin(vertex_index) index : u32,
};

fn factorial_ratio(l: i32, m: i32) -> f32 {
    if (m == 0 || l == 0) {
        return 1.0;
    }
    var result = 1.0;
    let start = l - m + 1;
    let stop = l + m;
    if (stop < start) {
        return 1.0;
    }
    for (var k: i32 = start; k <= stop; k++) {
        result /= f32(k);
    }
    return result;
}

fn legendre_index(l: i32, m: i32) -> u32 {
    return u32(l) * SH_STRIDE + u32(m);
}

fn get_active_coeff_count() -> i32 {
    if (NUM_COEFFS == 0) {
        return 0;
    }
    if (u_material.n_coeffs != -1) {
        if (u_material.n_coeffs < NUM_COEFFS) {
            return u_material.n_coeffs;
        }
        return NUM_COEFFS;
    }
    return NUM_COEFFS;
}

fn clamp_radius(value: f32) -> f32 {
    return abs(value) * u_material.scale;
}

fn cubic_interp(t: f32, p0: f32, p1: f32, p2: f32, p3: f32) -> f32 {
    let a = -0.5 * p0 + 1.5 * p1 - 1.5 * p2 + 0.5 * p3;
    let b = p0 - 2.5 * p1 + 2.0 * p2 - 0.5 * p3;
    let c = -0.5 * p0 + 0.5 * p2;
    let d = p1;
    return ((a * t + b) * t + c) * t + d;
}

fn sample_radius_lut_bicubic(glyph_id: u32, direction: vec3<f32>) -> f32 {
    if (LUT_PHI_RES == 0u || LUT_THETA_RES == 0u || LUT_STRIDE == 0u) {
        return 0.0;
    }
    
    let theta = acos(clamp(direction.z, -1.0, 1.0));
    let phi = atan2(direction.y, direction.x);
    
    let u = (phi + PI) / (2.0 * PI);
    let v = theta / PI;
    
    let x = u * f32(LUT_PHI_RES);
    let theta_max = max(LUT_THETA_RES, 1u) - 1u;
    let y = v * f32(theta_max);
    
    let x1_raw = u32(floor(x)) % LUT_PHI_RES;
    let y1 = u32(floor(y));
    
    let x0 = (x1_raw + LUT_PHI_RES - 1u) % LUT_PHI_RES;
    let x1 = x1_raw;
    let x2 = (x1_raw + 1u) % LUT_PHI_RES;
    let x3 = (x1_raw + 2u) % LUT_PHI_RES;
    
    let y0 = clamp(i32(y1) - 1, 0, i32(theta_max));
    let y2 = min(y1 + 1u, theta_max);
    let y3 = min(y1 + 2u, theta_max);
    
    // Get fractional parts for interpolation
    let fx = fract(x);
    let fy = fract(y);
    
    // Calculate base offset for this glyph
    let base_offset = glyph_id * LUT_STRIDE;
    
    // Sample 4x4 grid (16 samples)
    // Row 0 (y0)
    let r00 = s_sh_radius_lut[base_offset + u32(y0) * LUT_PHI_RES + u32(x0)];
    let r10 = s_sh_radius_lut[base_offset + u32(y0) * LUT_PHI_RES + x1];
    let r20 = s_sh_radius_lut[base_offset + u32(y0) * LUT_PHI_RES + x2];
    let r30 = s_sh_radius_lut[base_offset + u32(y0) * LUT_PHI_RES + x3];
    
    // Row 1 (y1)
    let r01 = s_sh_radius_lut[base_offset + y1 * LUT_PHI_RES + u32(x0)];
    let r11 = s_sh_radius_lut[base_offset + y1 * LUT_PHI_RES + x1];
    let r21 = s_sh_radius_lut[base_offset + y1 * LUT_PHI_RES + x2];
    let r31 = s_sh_radius_lut[base_offset + y1 * LUT_PHI_RES + x3];
    
    // Row 2 (y2)
    let r02 = s_sh_radius_lut[base_offset + y2 * LUT_PHI_RES + u32(x0)];
    let r12 = s_sh_radius_lut[base_offset + y2 * LUT_PHI_RES + x1];
    let r22 = s_sh_radius_lut[base_offset + y2 * LUT_PHI_RES + x2];
    let r32 = s_sh_radius_lut[base_offset + y2 * LUT_PHI_RES + x3];
    
    // Row 3 (y3)
    let r03 = s_sh_radius_lut[base_offset + y3 * LUT_PHI_RES + u32(x0)];
    let r13 = s_sh_radius_lut[base_offset + y3 * LUT_PHI_RES + x1];
    let r23 = s_sh_radius_lut[base_offset + y3 * LUT_PHI_RES + x2];
    let r33 = s_sh_radius_lut[base_offset + y3 * LUT_PHI_RES + x3];
    
    // Interpolate in x direction (4 cubic interpolations)
    let cy0 = cubic_interp(fx, r00, r10, r20, r30);
    let cy1 = cubic_interp(fx, r01, r11, r21, r31);
    let cy2 = cubic_interp(fx, r02, r12, r22, r32);
    let cy3 = cubic_interp(fx, r03, r13, r23, r33);
    
    // Interpolate in y direction (1 cubic interpolation)
    let radius = cubic_interp(fy, cy0, cy1, cy2, cy3);
    
    return radius;
}

fn sample_radius_lut(glyph_id: u32, direction: vec3<f32>) -> f32 {
    if (LUT_PHI_RES == 0u || LUT_THETA_RES == 0u || LUT_STRIDE == 0u) {
        return 0.0;
    }
    
    let theta = acos(clamp(direction.z, -1.0, 1.0));
    let phi = atan2(direction.y, direction.x);
    
    let u = (phi + PI) / (2.0 * PI);
    let v = theta / PI;
    
    let x = u * f32(LUT_PHI_RES);
    let y = v * f32(max(LUT_THETA_RES, 1u) - 1u);  // Non-periodic: use resolution-1
    
    // Get integer indices
    let x0_raw = u32(floor(x)) % LUT_PHI_RES;  // Wrap immediately
    let y0 = u32(floor(y));
    
    // Get neighbor indices with proper boundary conditions
    // Phi wraps (periodic)
    let x0 = x0_raw;
    let x1 = (x0_raw + 1u) % LUT_PHI_RES;
    // Theta clamps (non-periodic)
    let theta_max = max(LUT_THETA_RES, 1u) - 1u;
    let y1 = min(y0 + 1u, theta_max);
    
    // Get fractional parts for interpolation
    let fx = fract(x);
    let fy = fract(y);
    
    // Apply smootherstep (Ken Perlin's 5th order) for ultra-smooth interpolation
    // This is C2 continuous (smooth second derivative) - eliminates visible steps
    // Formula: 6t^5 - 15t^4 + 10t^3
    let fx_smooth = fx * fx * fx * (fx * (fx * 6.0 - 15.0) + 10.0);
    let fy_smooth = fy * fy * fy * (fy * (fy * 6.0 - 15.0) + 10.0);
    
    // Calculate base offset for this glyph
    let base_offset = glyph_id * LUT_STRIDE;
    
    let r00 = s_sh_radius_lut[base_offset + y0 * LUT_PHI_RES + x0];
    let r10 = s_sh_radius_lut[base_offset + y0 * LUT_PHI_RES + x1];
    let r01 = s_sh_radius_lut[base_offset + y1 * LUT_PHI_RES + x0];
    let r11 = s_sh_radius_lut[base_offset + y1 * LUT_PHI_RES + x1];
    
    let r0 = mix(r00, r10, fx_smooth);
    let r1 = mix(r01, r11, fx_smooth);
    let radius = mix(r0, r1, fy_smooth);
    
    return radius;
}

fn get_radius_optimized(glyph_id: u32, coeff_offset: i32, direction: vec3<f32>, coeff_limit: i32) -> f32 {
    if (USE_PRECOMPUTED_RADIUS_LUT && LUT_STRIDE > 0u) {
        if (USE_BICUBIC_INTERPOLATION) {
            return sample_radius_lut_bicubic(glyph_id, direction);
        } else {
            return sample_radius_lut(glyph_id, direction);
        }
    } else {
        return evaluate_radius(coeff_offset, direction, coeff_limit);
    }
}

fn evaluate_radius(coeff_offset: i32, direction: vec3<f32>, coeff_limit: i32) -> f32 {
    if (coeff_limit <= 0) {
        return 0.0;
    }

    var idx = coeff_offset;
    var used = 0;
    var sum = 0.0;

    let phi = atan2(direction.y, direction.x);
    let cos_theta = clamp(direction.z, -1.0, 1.0);

    let sin_theta = sqrt(max(0.0, 1.0 - cos_theta * cos_theta));

    var cos_table: array<f32, SH_TRIG_SIZE>;
    var sin_table: array<f32, SH_TRIG_SIZE>;
    cos_table[0u] = 1.0;
    sin_table[0u] = 0.0;
    if (L_MAX >= 1) {
        let cos_phi = cos(phi);
        let sin_phi = sin(phi);
        cos_table[1u] = cos_phi;
        sin_table[1u] = sin_phi;
        for (var m: i32 = 2; m <= L_MAX; m = m + 1) {
            let prev_cos = cos_table[u32(m - 1)];
            let prev_sin = sin_table[u32(m - 1)];
            cos_table[u32(m)] = prev_cos * cos_phi - prev_sin * sin_phi;
            sin_table[u32(m)] = prev_sin * cos_phi + prev_cos * sin_phi;
        }
    }

    var norm_p_table: array<f32, SH_TABLE_SIZE>;

    for (var m: i32 = 0; m <= L_MAX; m = m + 1) {
        var pmm = 1.0;
        if (m > 0) {
            var fact = 1.0;
            let somx2 = sin_theta;
            for (var i: i32 = 1; i <= m; i = i + 1) {
                pmm *= -fact * somx2;
                fact += 2.0;
            }
        }

        var ratio = factorial_ratio(m, m);
        let idx_mm = legendre_index(m, m);
        let norm_mm = sqrt(((2.0 * f32(m) + 1.0) / (4.0 * PI)) * ratio);
        norm_p_table[idx_mm] = pmm * norm_mm;

        var prev_prev = pmm;
        var prev = pmm;
        if (m < L_MAX) {
            var pmmp1 = cos_theta * (2.0 * f32(m) + 1.0) * pmm;
            let l1 = m + 1;
            ratio = ratio * f32(l1 - m) / f32(l1 + m);
            let norm1 = sqrt(((2.0 * f32(l1) + 1.0) / (4.0 * PI)) * ratio);
            norm_p_table[legendre_index(l1, m)] = pmmp1 * norm1;
            prev_prev = pmm;
            prev = pmmp1;

            for (var l: i32 = m + 2; l <= L_MAX; l = l + 1) {
                let ll_f = f32(l);
                let value = ((2.0 * ll_f - 1.0) * cos_theta * prev -
                    (ll_f + f32(m) - 1.0) * prev_prev) /
                    (ll_f - f32(m));
                prev_prev = prev;
                prev = value;
                ratio = ratio * f32(l - m) / f32(l + m);
                let norm_l = sqrt(((2.0 * ll_f + 1.0) / (4.0 * PI)) * ratio);
                norm_p_table[legendre_index(l, m)] = value * norm_l;
            }
        }
    }

    for (var l: i32 = 0; l <= L_MAX; l = l + 1) {
        for (var m: i32 = -l; m <= l; m = m + 1) {
            if (used >= coeff_limit) {
                return sum;
            }

            let abs_m = abs(m);
            let base = norm_p_table[legendre_index(l, abs_m)];
            var sh = base;
            if (abs_m > 0) {
                let cos_m = cos_table[u32(abs_m)];
                let sin_m = sin_table[u32(abs_m)];
                if (m > 0) {
                    sh = base * SQRT_2 * cos_m;
                } else {
                    sh = base * SQRT_2 * sin_m;
                }
            }

            sum += s_coeffs[idx] * sh;
            idx += 1;
            used += 1;
        }
    }

    return sum;
}

const BISECTION_STEPS: i32 = 12;
const NEWTON_STEPS: i32 = 3;
const RAY_BRACKET_STEPS: i32 = 48;

struct IntersectionResult {
    hit: bool,
    position: vec3<f32>,
    direction: vec3<f32>,
    raw_radius: f32,
};

fn surface_difference(
    coeff_offset: i32,
    center: vec3<f32>,
    ray_origin: vec3<f32>,
    ray_dir: vec3<f32>,
    t: f32,
    coeff_limit: i32,
    glyph_id: u32,
) -> f32 {
    let position = ray_origin + ray_dir * t;
    let offset = position - center;
    let dist = length(offset);
    if (dist < 1e-5) {
        let raw_radius = get_radius_optimized(glyph_id, coeff_offset, normalize(ray_dir), coeff_limit);
        return -clamp_radius(raw_radius);
    }
    let direction = offset / dist;
    let raw_radius = get_radius_optimized(glyph_id, coeff_offset, direction, coeff_limit);
    let radius = clamp_radius(raw_radius);
    return dist - radius;
}

fn evaluate_implicit(
    coeff_offset: i32,
    center: vec3<f32>,
    point: vec3<f32>,
    coeff_limit: i32,
    glyph_id: u32,
) -> f32 {
    let offset = point - center;
    let dist = length(offset);
    if (dist < 1e-5) {
        let fallback_dir = normalize(vec3<f32>(0.577, 0.577, 0.577));
        let raw_radius = get_radius_optimized(glyph_id, coeff_offset, fallback_dir, coeff_limit);
        let radius = clamp_radius(raw_radius);
        return dist - radius;
    }
    let direction = offset / dist;
    let raw_radius = get_radius_optimized(glyph_id, coeff_offset, direction, coeff_limit);
    let radius = clamp_radius(raw_radius);
    return dist - radius;
}

fn estimate_surface_normal(
    coeff_offset: i32,
    center: vec3<f32>,
    point: vec3<f32>,
    coeff_limit: i32,
    glyph_id: u32,
) -> vec3<f32> {
    let scale = max(length(point - center) * 1e-3, 1e-3);
    let offsets = array<vec3<f32>, 3>(
        vec3<f32>(scale, 0.0, 0.0),
        vec3<f32>(0.0, scale, 0.0),
        vec3<f32>(0.0, 0.0, scale),
    );

    var gradient = vec3<f32>(0.0);
    for (var axis: i32 = 0; axis < 3; axis = axis + 1) {
        let o = offsets[axis];
        let pos_plus = evaluate_implicit(coeff_offset, center, point + o, coeff_limit, glyph_id);
        let pos_minus = evaluate_implicit(coeff_offset, center, point - o, coeff_limit, glyph_id);
        gradient[axis] = (pos_plus - pos_minus) / (2.0 * scale);
    }

    if (length(gradient) < 1e-5) {
        return normalize(point - center);
    }
    return normalize(gradient);
}

fn find_surface_intersection(
    coeff_offset: i32,
    center: vec3<f32>,
    ray_origin: vec3<f32>,
    ray_dir: vec3<f32>,
    bound_radius: f32,
    coeff_limit: i32,
    glyph_id: u32,
) -> IntersectionResult {
    var result: IntersectionResult;
    result.hit = false;
    result.position = vec3<f32>(0.0);
    result.direction = vec3<f32>(0.0);
    result.raw_radius = 0.0;

    if (bound_radius <= 1e-5) {
        return result;
    }

    let oc = ray_origin - center;
    let a = dot(ray_dir, ray_dir);
    let b = dot(oc, ray_dir);
    let c = dot(oc, oc) - bound_radius * bound_radius;
    var discriminant = b * b - a * c;
    if (discriminant < 0.0) {
        if (discriminant > -1e-4) {
            discriminant = 0.0;
        } else {
            return result;
        }
    }
    let sqrt_disc = sqrt(max(discriminant, 0.0));
    let inv_a = 1.0 / a;
    var t_near = (-b - sqrt_disc) * inv_a;
    var t_far = (-b + sqrt_disc) * inv_a;
    if (t_far < 0.0) {
        return result;
    }
    if (t_near < 0.0) {
        t_near = 0.0;
    }

    var start = t_near;
    var end = t_far;
    if (end <= start) {
        end = start + bound_radius;
    }

    var prev_t = start;
    var prev_val = surface_difference(coeff_offset, center, ray_origin, ray_dir, start, coeff_limit, glyph_id);

    var bracket_low = start;
    var bracket_high = end;
    var found = false;

    for (var step: i32 = 1; step <= RAY_BRACKET_STEPS; step = step + 1) {
        let t = start + (end - start) * f32(step) / f32(RAY_BRACKET_STEPS);
        let val = surface_difference(coeff_offset, center, ray_origin, ray_dir, t, coeff_limit, glyph_id);

        if (!found) {
            if (prev_val <= 0.0 && val > 0.0) {
                prev_t = t;
                prev_val = val;
                continue;
            }

            if (prev_val > 0.0 && val <= 0.0) {
                bracket_low = prev_t;
                bracket_high = t;
                found = true;
                break;
            }
        }

        prev_t = t;
        prev_val = val;
    }

    if (!found) {
        return result;
    }

    for (var i: i32 = 0; i < BISECTION_STEPS; i = i + 1) {
        let mid = 0.5 * (bracket_low + bracket_high);
        let val = surface_difference(coeff_offset, center, ray_origin, ray_dir, mid, coeff_limit, glyph_id);
        if (val <= 0.0) {
            bracket_high = mid;
        } else {
            bracket_low = mid;
        }
    }

    var t = 0.5 * (bracket_low + bracket_high);
    for (var i: i32 = 0; i < NEWTON_STEPS; i = i + 1) {
        let diff = surface_difference(coeff_offset, center, ray_origin, ray_dir, t, coeff_limit, glyph_id);
        let epsilon = max(1e-4 * (bracket_high - bracket_low + 1.0), 1e-4);
        let diff_next = surface_difference(
            coeff_offset,
            center,
            ray_origin,
            ray_dir,
            t + epsilon,
            coeff_limit,
            glyph_id,
        );
        let derivative = (diff_next - diff) / epsilon;
        if (abs(derivative) < 1e-5) {
            break;
        }
        let new_t = clamp(t - diff / derivative, bracket_low, bracket_high);
        if (abs(new_t - t) < 1e-4 * max(bracket_high - bracket_low, 1.0)) {
            t = new_t;
            break;
        }
        t = new_t;
    }

    let position = ray_origin + ray_dir * t;
    let direction = normalize(position - center);
    result.hit = true;
    result.position = position;
    result.direction = direction;
    result.raw_radius = get_radius_optimized(glyph_id, coeff_offset, direction, coeff_limit);
    return result;
}

@vertex
fn vs_main(in: VertexInput) -> Varyings {
    let billboard_index = i32(in.index) / 6;
    let vertex_in_quad = i32(in.index) % 6;

    var local_pos: vec2<f32>;
    switch vertex_in_quad {
        case 0: { local_pos = vec2<f32>(-0.5, -0.5); }
        case 1: { local_pos = vec2<f32>(0.5, -0.5); }
        case 2: { local_pos = vec2<f32>(-0.5, 0.5); }
        case 3: { local_pos = vec2<f32>(0.5, -0.5); }
        case 4: { local_pos = vec2<f32>(0.5, 0.5); }
        default: { local_pos = vec2<f32>(-0.5, 0.5); }
    }

    let raw_center = load_s_positions(billboard_index * 6);
    let world_center = u_wobject.world_transform * vec4<f32>(raw_center.xyz, 1.0);

    let cam_right = vec3<f32>(u_stdinfo.cam_transform_inv[0].xyz);
    let cam_up = vec3<f32>(u_stdinfo.cam_transform_inv[1].xyz);

    let raw_size = load_s_normals(billboard_index * 6);
    let size = raw_size.xy;

    let billboard_offset = local_pos.x * cam_right * size.x + local_pos.y * cam_up * size.y;
    let world_pos = world_center.xyz + billboard_offset;

    let clip_pos = u_stdinfo.projection_transform * u_stdinfo.cam_transform * vec4<f32>(world_pos, 1.0);

    var tex_coord: vec2<f32>;
    switch vertex_in_quad {
        case 0: { tex_coord = vec2<f32>(0.0, 0.0); }
        case 1: { tex_coord = vec2<f32>(1.0, 0.0); }
        case 2: { tex_coord = vec2<f32>(0.0, 1.0); }
        case 3: { tex_coord = vec2<f32>(1.0, 0.0); }
        case 4: { tex_coord = vec2<f32>(1.0, 1.0); }
        default: { tex_coord = vec2<f32>(0.0, 1.0); }
    }

    var varyings: Varyings;
    varyings.position = vec4<f32>(clip_pos);
    varyings.world_pos = vec3<f32>(world_pos);
    let color = load_s_colors(billboard_index * 6);
    varyings.color = vec4<f32>(color, 1.0);
    varyings.texcoord_vert = vec2<f32>(tex_coord);
    varyings.billboard_center = vec3<f32>(world_center.xyz);
    varyings.billboard_right = vec3<f32>(cam_right.xyz);
    varyings.billboard_up = vec3<f32>(cam_up.xyz);
    varyings.billboard_size = vec2<f32>(size);
    varyings.billboard_index = f32(billboard_index);

    return varyings;
}

struct ReflectedLight {
    direct_diffuse: vec3<f32>,
    direct_specular: vec3<f32>,
    indirect_diffuse: vec3<f32>,
    indirect_specular: vec3<f32>,
};

@fragment
fn fs_main(varyings: Varyings, @builtin(front_facing) is_front: bool) -> FragmentOutput {
    {$ include 'pygfx.clipping_planes.wgsl' $}

    let uv = varyings.texcoord_vert.xy;
    let coord = uv * 2.0 - vec2<f32>(1.0);
    let radius_sq = dot(coord, coord);
    if (radius_sq > 1.0) {
        discard;
    }

    let smooth_edge = fwidth(radius_sq);
    let mask = clamp(1.0 - smoothstep(1.0 - smooth_edge, 1.0 + smooth_edge, radius_sq), 0.0, 1.0);

    let center = varyings.billboard_center;
    let plane_pos = varyings.world_pos;
    let cam_pos = u_stdinfo.cam_transform_inv[3].xyz;
    let cam_forward = normalize((u_stdinfo.cam_transform_inv * vec4<f32>(0.0, 0.0, -1.0, 0.0)).xyz);
    let ortho = is_orthographic();

    var ray_origin = cam_pos;
    var ray_dir = plane_pos - cam_pos;
    if (ortho) {
        ray_origin = plane_pos;
        ray_dir = -cam_forward;
    } else {
        let dir_len = length(ray_dir);
        if (dir_len > 0.0) {
            ray_dir = ray_dir / dir_len;
        } else {
            ray_dir = cam_forward;
        }
    }
    ray_dir = normalize(ray_dir);

    let coeff_limit = get_active_coeff_count();
    if (coeff_limit <= 0 || NUM_COEFFS == 0) {
        discard;
    }

    let billboard_index = max(i32(round(varyings.billboard_index)), 0);
    let coeff_offset = billboard_index * NUM_COEFFS;
    let glyph_id = u32(billboard_index);

    let bound_radius = 0.5 * max(varyings.billboard_size.x, varyings.billboard_size.y);
    let intersection = find_surface_intersection(
        coeff_offset,
        center,
        ray_origin,
        ray_dir,
        bound_radius,
        coeff_limit,
        glyph_id,
    );

    if (!intersection.hit) {
        discard;
    }

    var direction = normalize(intersection.direction);
    let raw_radius = intersection.raw_radius;
    let surface_radius = clamp_radius(raw_radius);

    var world_pos = intersection.position;
    let dist_to_center = length(world_pos - center);
    if (abs(dist_to_center - surface_radius) > max(1e-3, 1e-3 * surface_radius)) {
        world_pos = center + direction * surface_radius;
    }

    var world_normal = estimate_surface_normal(
        coeff_offset,
        center,
        world_pos,
        coeff_limit,
        glyph_id,
    );

    if (!is_front) {
        world_normal = -world_normal;
    }

    let clip_pos = u_stdinfo.projection_transform * u_stdinfo.cam_transform * vec4<f32>(world_pos, 1.0);
    var view_dir = normalize(cam_pos - world_pos);
    if (ortho) {
        view_dir = normalize(-ray_dir);
    }

    var glyph_color = vec3<f32>(1.0);
    if (COLOR_TYPE == 0) {
        if (raw_radius < 0.0) {
            glyph_color = vec3<f32>(0.0, 0.0, 1.0);
        } else {
            glyph_color = vec3<f32>(1.0, 0.0, 0.0);
        }
    } else {
        glyph_color = abs(normalize(direction));
    }

    glyph_color = clamp(glyph_color * varyings.color.rgb, vec3<f32>(0.0), vec3<f32>(1.0));

    var diffuse_color = vec4<f32>(srgb2physical(glyph_color), 1.0);
    diffuse_color.a *= u_material.opacity * mask;
    do_alpha_test(diffuse_color.a);

    let physical_albedo = diffuse_color.rgb;
    let specular_strength = 1.0;

    var reflected_light: ReflectedLight = ReflectedLight(
        vec3<f32>(0.0),
        vec3<f32>(0.0),
        vec3<f32>(0.0),
        vec3<f32>(0.0),
    );

    var geometry: GeometricContext;
    geometry.position = world_pos;
    geometry.normal = world_normal;
    geometry.view_dir = view_dir;

    var material: BlinnPhongMaterial;
    material.diffuse_color = physical_albedo;
    material.specular_color = srgb2physical(u_material.specular_color.rgb);
    material.specular_shininess = u_material.shininess;
    material.specular_strength = specular_strength;

    let ambient_color = u_ambient_light.color.rgb;
    var irradiance = getAmbientLightIrradiance(ambient_color);
    RE_IndirectDiffuse(irradiance, geometry, material, &reflected_light);

    {$ include 'pygfx.light_punctual.wgsl' $}

    var emissive_color = srgb2physical(u_material.emissive_color.rgb) * u_material.emissive_intensity;

    var physical_color = reflected_light.direct_diffuse +
        reflected_light.direct_specular +
        reflected_light.indirect_diffuse +
        reflected_light.indirect_specular +
        emissive_color;

    if (all(physical_color == vec3<f32>(0.0))) {
        let fallback_light = normalize(vec3<f32>(0.3, 0.5, 0.8));
        let fallback_diffuse = max(dot(world_normal, fallback_light), 0.0);
        physical_color = physical_albedo * clamp(0.3 + 0.7 * fallback_diffuse, 0.0, 1.0);
    }

    var out: FragmentOutput;
    out.color = vec4<f32>(physical_color, diffuse_color.a);
    let ndc = clip_pos / clip_pos.w;
    out.depth = ndc.z;
    return out;
}
