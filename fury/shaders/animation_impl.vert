
// vertexVCVSOutput = MCVCMatrix * vertexMC;
////
vec3 f_scale = vec3(1, 1, 1);
vec3 f_position = vec3(0, 0, 0);

if (is_interpolatable(scale_k))
    f_scale = interp(scale_k, time);

if (is_interpolatable(color_k))
    vertexColorVSOutput = vec4(interp(color_k, time), 1);
else
    vertexColorVSOutput = scalarColor;

if (is_interpolatable(position_k))
    f_position = interp(position_k, time);

Keyframes pos =  position_k;
gl_Position = MCDCMatrix * transformation(f_position, f_scale) * vertexMC ;