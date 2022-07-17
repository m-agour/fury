/* SDF fragment shader implementation */

//VKT::Light::Impl

vec3 point = vertexMCVSOutput.xyz;

//ray origin
vec4 ro = -MCVCMatrix[3] * MCVCMatrix;  // camera position in world space

vec3 col = vertexColorVSOutput.rgb;

//ray direction
vec3 rd = normalize(point - ro.xyz);

vec3 eye = ro.xyz;
ro += vec4((point - eye),0.0);

//light direction
vec3 ld = -rd;

float t = castRay(ro.xyz, rd);
    
if(t < 20.0)
{
    vec3 position = ro.xyz + t * rd;
    vec3 norm = calculateNormal(position);
    float light = dot(ld, norm);

    vec3 frag = col * light;

    int antialiasing = 0;
    float antialiasing_factor = 0.2;
    if (antialiasing != 0){
        // dot product between (ray from eye to point) and the normal to that point
        float ed = abs(dot(norm, normalize(point - eye)));
        if(ed < antialiasing_factor) fragOutput0 = vec4(frag, mix(0, 1,  ed/antialiasing_factor));
        else  fragOutput0 = vec4(frag, 1.0);
    }
    else fragOutput0 = vec4(frag, 1.0);

    	
}
else{
    
    discard;
}
