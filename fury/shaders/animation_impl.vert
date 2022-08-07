
// vertexVCVSOutput = MCVCMatrix * vertexMC;

vec3 f_scale = vec3(1, 1, 1);
if (is_interpolatable(scale_k))
    f_scale = interp(scale_k, time);

if (is_interpolatable(color_k))
    vertexColorVSOutput = vec4(interp(color_k, time), 1);
else
    vertexColorVSOutput = scalarColor;

vertexColorVSOutput = scalarColor;
Keyframes pos =  position_k;
gl_Position = MCDCMatrix * transformation(interp(pos, time), f_scale) * vertexMC ;