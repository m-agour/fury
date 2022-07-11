/* SDF fragment shader implementation */

//VKT::Light::Impl

vec3 point = vertexMCVSOutput.xyz;

//ray origin
vec4 ro = -MCVCMatrix[3] * MCVCMatrix;  // camera position in world space

vec3 col = vertexColorVSOutput.rgb;

//ray direction
vec3 rd = normalize(point - ro.xyz);
//light direction
vec3 ld = ro.xyz - point;
ro += vec4((point - ro.xyz),0.0);



float t = castRay(ro.xyz, rd);
    
if(t < 20.0)
{
    vec3 position = ro.xyz + t * rd;
    vec3 norm = calculateNormal(position);
    float light = dot(ld, norm);

    fragOutput0 = vec4(col * light * 0.01, 1.0);
    	
}
else{
    
    discard;
}
