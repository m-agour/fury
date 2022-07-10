import math
import time
from collections import defaultdict

import numpy as np
from scipy import interpolate
from vtkmodules.vtkCommonCore import reference

from fury import utils
from fury.colormap import rgb2hsv, hsv2rgb, rgb2lab, lab2rgb, xyz2rgb, rgb2xyz
from fury.shaders import shader_to_actor, add_shader_callback


class Keyframe:
    def __init__(self, timestamp, data, pre_cp=None, post_cp=None):
        self.timestamp = timestamp
        self.data = data
        self.pre_cp = pre_cp
        self.post_cp = post_cp


class Interpolator(object):
    def __init__(self, keyframes):
        super(Interpolator, self).__init__()
        self.keyframes = keyframes
        self.timestamps = []
        self.setup()

    def setup(self):
        self.timestamps = np.sort(np.array(list(self.keyframes)), axis=None)

    def _get_nearest_smaller_timestamp(self, t):
        try:
            return self.timestamps[self.timestamps <= t].max()
        except:
            if self.timestamps is not []:
                return self.timestamps[0]
            else:
                return None

    def _get_nearest_larger_timestamp(self, t):
        try:
            return self.timestamps[self.timestamps > t].min()
        except:
            if self.timestamps is not []:
                return self.timestamps[-1]
            else:
                return None

    def get_neighbour_timestamps(self, t):
        t1 = self._get_nearest_smaller_timestamp(t)
        t2 = self._get_nearest_larger_timestamp(t)
        return t1, t2

    def get_neighbour_keyframes(self, t):
        t_s, t_e = self.get_neighbour_timestamps(t)
        if isinstance(self, ColorInterpolator):
            k1 = {"t": t_s, "data": self.space_keyframes[t_s]}
            k2 = {"t": t_e, "data": self.space_keyframes[t_e]}
        else:
            k1 = {"t": t_s, "data": self.keyframes[t_s]}
            k2 = {"t": t_e, "data": self.keyframes[t_e]}
        if isinstance(self, BezierInterpolator):
            k1["cp"] = self.post_cps[t_s]
            k2["cp"] = self.pre_cps[t_e]
        return {"start": k1, "end": k2}

    @staticmethod
    def lerp(v1, v2, t1, t2, t):
        if t1 == t2:
            return v1
        v = v2 - v1
        dt = (t - t1) / (t2 - t1)
        return dt * v + v1


class StepInterpolator(Interpolator):
    """Step interpolator for keyframes.

    This is a simple step interpolator to be used for any shape of
    keyframes data.
    """

    def __init__(self, keyframes):
        super(StepInterpolator, self).__init__(keyframes)
        self.id = 0

    def setup(self):
        super(StepInterpolator, self).setup()

    def interpolate(self, t):
        t_lower = self._get_nearest_smaller_timestamp(t)
        return self.keyframes[t_lower]


class LinearInterpolator(Interpolator):
    """Linear interpolator for keyframes.

    This is a general linear interpolator to be used for any shape of
    keyframes data.
    """

    def __init__(self, keyframes=None):
        if keyframes is None:
            keyframes = {}
        super(LinearInterpolator, self).__init__(keyframes)
        self.id = 1

    def setup(self):
        super(LinearInterpolator, self).setup()

    def interpolate(self, t):
        t1 = self._get_nearest_smaller_timestamp(t)
        t2 = self._get_nearest_larger_timestamp(t)
        p1 = self.keyframes[t1]
        p2 = self.keyframes[t2]
        return self.lerp(p1, p2, t1, t2, t)


class SplineInterpolator(Interpolator):
    """N-th degree spline interpolator for keyframes.

    This is a general n-th degree spline interpolator to be used for any shape
    of keyframes data.
    """

    def __init__(self, keyframes, degree=3, smoothness=3):
        self.degree = degree
        self.smoothness = smoothness
        self.tck = []
        self.linear_lengths = []
        super(SplineInterpolator, self).__init__(keyframes)
        self.id = 6

    def setup(self):
        super(SplineInterpolator, self).setup()
        points = np.asarray(self.get_points())

        if len(points) < (self.degree + 1):
            raise ValueError(f"Minimum {self.degree + 1} "
                             f"keyframes must be set in order to use "
                             f"{self.degree}-degree spline")

        self.tck = interpolate.splprep(points.T, k=self.degree, full_output=1,
                                       s=self.smoothness)[0][0]
        self.linear_lengths = []
        for x, y in zip(points, points[1:]):
            self.linear_lengths.append(
                math.sqrt((x[1] - y[1]) * (x[1] - y[1]) +
                          (x[0] - y[0]) * (x[0] - y[0])))

    def get_points(self):
        return [self.keyframes[i] for i in sorted(self.keyframes.keys())]

    def interpolate(self, t):
        t1 = self._get_nearest_smaller_timestamp(t)
        t2 = self._get_nearest_larger_timestamp(t)
        if t1 == t2:
            return self.keyframes[t1]

        dt = (t - t1) / (t2 - t1)
        mi_index = np.where(self.timestamps == t1)[0][0]

        sect = sum(self.linear_lengths[:mi_index])
        t = (sect + dt * (self.linear_lengths[mi_index])) / sum(
            self.linear_lengths)
        return np.array(interpolate.splev(t, self.tck))


class CubicSplineInterpolator(SplineInterpolator):
    """Cubic spline interpolator for keyframes.

    This is a general cubic spline interpolator to be used for any shape of
    keyframes data.
    """

    def __init__(self, keyframes, smoothness=3):
        super(CubicSplineInterpolator, self).__init__(keyframes, degree=3,
                                                      smoothness=smoothness)
        self.id = 7


class BezierInterpolator(Interpolator):
    """Cubic bezier interpolator for keyframes.

    This is a general cubic bezier interpolator to be used for any shape of
    keyframes data.
    """

    def __init__(self, keyframes, pre_cps, post_cps):
        self.pre_cps = pre_cps
        self.post_cps = post_cps
        super(BezierInterpolator, self).__init__(keyframes)
        self.id = 2

    def setup(self):
        super(BezierInterpolator, self).setup()
        for ts in self.timestamps:
            if self.pre_cps[ts] is None:
                self.pre_cps[ts] = self.keyframes[ts]
            if self.post_cps[ts] is None:
                self.post_cps[ts] = self.keyframes[ts]

    def interpolate(self, t):
        t1, t2 = self.get_neighbour_timestamps(t)
        p0 = self.keyframes[t1]
        p1 = self.post_cps[t1]
        p2 = self.pre_cps[t2]
        p3 = self.keyframes[t2]
        if t2 == t1:
            return p0
        dt = (t - t1) / (t2 - t1)
        res = (1 - dt) ** 3 * p0 + 3 * (1 - dt) ** 2 * dt * p1 + 3 * \
              (1 - dt) * dt ** 2 * p2 + dt ** 3 * p3
        return res


class ColorInterpolator(Interpolator):
    def __init__(self, keyframes, rgb_to_space, space_to_rgb):
        self.rgb_to_space = rgb_to_space
        self.space_to_rgb = space_to_rgb
        self.space_keyframes = {}
        super(ColorInterpolator, self).__init__(keyframes)

    def setup(self):
        super(ColorInterpolator, self).setup()
        for key, value in self.keyframes.items():
            self.space_keyframes[key] = self.rgb_to_space(value)

    def interpolate(self, t):
        t1, t2 = self.get_neighbour_timestamps(t)
        p1 = self.space_keyframes[t1]
        p2 = self.space_keyframes[t2]
        lab_val = self.lerp(p1, p2, t1, t2, t)
        return self.space_to_rgb(lab_val)


class HSVInterpolator(ColorInterpolator):
    """LAB interpolator for color keyframes """

    def __init__(self, keyframes):
        super().__init__(keyframes, rgb2hsv, hsv2rgb)
        self.id = 3


class XYZInterpolator(ColorInterpolator):
    """XYZ interpolator for color keyframes """

    def __init__(self, keyframes):
        super().__init__(keyframes, rgb2xyz, xyz2rgb)
        self.id = 4


class LABInterpolator(ColorInterpolator):
    """LAB interpolator for color keyframes """

    def __init__(self, keyframes):
        super().__init__(keyframes, rgb2lab, lab2rgb)
        self.id = 5


# Shaders for doing the animation
vertex_shader_code_decl = \
    """
    // uniform float time;
    mat3 xyz_to_rgb_mat = mat3( 3.24048134, -1.53715152, -0.49853633,
                               -0.96925495,  1.87599   ,  0.04155593,
                                0.05564664, -0.20404134,  1.05731107);
                             
    // Interpolation methods
    const int STEP = 0;
    const int LINEAR = 1;
    const int BEZIER = 2;
    const int HSV = 3;
    const int XYZ = 4;

    struct Keyframe {
        float t;
        vec3 data;  
        vec3 cp;
    };
    
    struct Keyframes {
        Keyframe start;
        Keyframe end;
        int method;
    };
    
        
    uniform Keyframes position_k;
    uniform Keyframes scale_k;
    uniform Keyframes color_k; 

    
    out float t;
    out vec4 vertexColorVSOutput;
    
    bool check_exact(Keyframes k){
        if (k.start.t == k.end.t || t > k.end.t)
        return true;
        return false;
    }
    
    vec3 lerp(Keyframes k){
        if (check_exact(k)) return k.end.data;
        float dt = (time - k.start.t) / (k.end.t - k.start.t);
        return mix(k.start.data, k.end.data, dt);
    }
    
    vec3 cubic_bezier(Keyframes k){
        if (check_exact(k)) return k.end.data;
        float t = (time - k.start.t) / (k.end.t - k.start.t);
        vec3 E = mix(k.start.data, k.start.cp, t);
        vec3 F = mix(k.start.cp, k.end.cp, t);
        vec3 G = mix(k.end.cp, k.end.data, t);
        
        vec3 H = mix(E, F, t);
        vec3 I = mix(F, G, t);
        
        vec3 P = mix(H, I, t);
        
        return P;
    }
    
    vec3 hsv2rgb(vec3 c)
    {
        vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
        vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
        return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
    }
            
    float clip(float x){
        if (x > 1)
        return 1;
        else if (x < 0)
        return 0;
        else return x;
    }
    vec3 xyz2rgb(vec3 c)
    {
        c = c * xyz_to_rgb_mat;
        float po = 1 / 2.4;
        if (c.x > 0.0031308) c.x = 1.055 * pow(c.x, po) - 0.055;
        else c.y *= 12.92;
        if (c.y > 0.0031308) c.y = 1.055 * pow(c.y, po) - 0.055;
        else c.y *= 12.92;
        if (c.z > 0.0031308) c.z = 1.055 * pow(c.z, po) - 0.055;
        else c.z *= 12.92;
        
        c.x = clip(c.x);
        c.y = clip(c.y);
        c.z = clip(c.z);
        
        return c;
    }
    
    vec3 lab2xyz(vec3 col)
    {
        float l = col.x;
        float a = col.y;
        float b = col.z;
        col.y = (l + 16.) / 116.;
        col.x = (a / 500.) + col.y;
        col.z = col.y - (b / 200.);
        return col;
    }
    
    vec3 interp(Keyframes k){
        if (k.method == LINEAR) return lerp(k);
        else if (k.method == BEZIER) return cubic_bezier(k);
        else if (k.method == HSV) return hsv2rgb(lerp(k));
        else if (k.method == XYZ) return xyz2rgb(lab2xyz(lerp(k)));

    }
    
    mat4 transformation(vec3 position, vec3 scale){
        return mat4(
            vec4(scale.x, 0.0, 0.0, 0.0),
            vec4(0.0, scale.y, 0.0, 0.0),
            vec4(0.0, 0.0, scale.z, 0.0),
            vec4(position, 1.0));
    }
    

    """

vertex_shader_code_impl = \
    """
    t = time;
    // vertexVCVSOutput = MCVCMatrix * vertexMC;
    vertexColorVSOutput = vec4(interp(color_k), 1);
    Keyframes pos =  position_k;
    gl_Position = MCDCMatrix * 
        transformation(interp(pos), interp(scale_k)) * vertexMC ;   
    """

fragment_shader_code_decl = \
    """
    //varying float t;
    """

fragment_shader_code_impl = \
    """
    fragOutput0 = vec4(1, 1, 1, 1.);
    """


class Timeline:
    """Keyframe animation timeline class.

    This timeline is responsible for keyframe animations for a single or a
    group of models.
    It's used to handle multiple attributes and properties of Fury actors such
    as transformations, color, and scale.
    It also accepts custom data and interpolates them such as temperature.
    Linear interpolation is used by default to interpolate data between main
    keyframes.
    """

    def __init__(self, actors=None, using_shaders=1):
        self._keyframes = {'position': {0: np.array([0, 0, 0])},
                           'rotation': {0: np.array([0, 0, 0])},
                           'scale': {0: np.array([1, 1, 1])},
                           'color': {0: np.array([1, 0, 0])}}
        self._interpolators = self._init_interpolators()
        self.playing = False
        self.loop = False
        self.reversePlaying = False
        self._last_started_at = 0
        self._last_timestamp = 0
        self._current_timestamp = 0
        self.speed = 1
        self._pre_cps = defaultdict(dict)
        self._post_cps = defaultdict(dict)
        if using_shaders:
            self.last_sent_timestamps = defaultdict(dict)
        # Handle actors while constructing the timeline.
        self._actors = []
        if actors is not None:
            if isinstance(actors, list):
                for a in actors:
                    a.vcolors = utils.colors_from_actor(a)
                    if using_shaders:
                        self._use_shader(a)
                    self._actors.append(a)
            else:
                actors.vcolors = utils.colors_from_actor(actors)
                if using_shaders:
                    self._use_shader(actors)
                self._actors = [actors]

        self._is_using_shaders = using_shaders

    def _use_shader(self, actor):
        shader_to_actor(actor, "vertex", impl_code=vertex_shader_code_impl)
        shader_to_actor(actor, "vertex", impl_code="",
                        block="color", replace_all=True, keep_default=False)
        shader_to_actor(actor, "vertex", decl_code=vertex_shader_code_decl,
                        block="prim_id")

        actor.GetShaderProperty().GetVertexCustomUniforms().SetUniformf(
            'time', 0)

        t_ref = reference(0)

        def shader_callback(_caller, _event, calldata=None):
            actor.GetShaderProperty().GetVertexCustomUniforms().GetUniformf(
                'time', t_ref)
            program = calldata
            if program is not None:
                if not self._is_using_shaders:
                    self.update(t_ref)
                    return
                try:
                    for attrib in ['position', 'scale', 'color']:
                        program.SetUniformi(f'{attrib}_k.method',
                                            self._interpolators[attrib].id)
                        timestamp = self._interpolators[attrib] \
                            .get_neighbour_timestamps(t_ref)
                        if self.last_sent_timestamps[attrib] == timestamp:
                            continue
                        self.last_sent_timestamps[attrib] = timestamp
                        keyframes = self._interpolators[attrib]. \
                            get_neighbour_keyframes(t_ref)

                        for kf in keyframes:
                            for field in keyframes[kf]:

                                if field == 't':
                                    program.SetUniformf(
                                        f'{attrib}_k.{kf}.{field}',
                                        keyframes[kf][field])
                                else:
                                    program.SetUniform3f(
                                        f'{attrib}_k.{kf}.{field}',
                                        keyframes[kf][field])
                except ValueError:
                    print('Error')

        add_shader_callback(actor, shader_callback)

    def _init_interpolators(self):
        return {'position': LinearInterpolator(self._keyframes["position"]),
                'rotation': LinearInterpolator(),
                'scale': LinearInterpolator(self._keyframes["scale"]),
                'color': LinearInterpolator(self._keyframes["color"])}

    def play(self):
        """Play the animation"""
        if not self.playing:
            self._last_started_at = time.perf_counter() - self._last_timestamp
            self.playing = True

    def pause(self):
        """Pause the animation"""
        self._last_timestamp = self.get_current_timestamp()
        self.playing = False

    def stop(self):
        """Stops the animation"""
        self._last_timestamp = 0
        self.playing = False

    def restart(self):
        """Restarts the animation"""
        self._last_timestamp = 0
        self.playing = True

    def get_current_timestamp(self):
        """Get current timestamp of the animation"""
        return (time.perf_counter() - self._last_started_at) if \
            self.playing else self._last_timestamp

    @property
    def last_timestamp(self):
        """Get the max timestamp of all keyframes"""
        return max(list(max(list(self._keyframes[i].keys()) for i in
                            self._keyframes.keys())))

    def set_timestamp(self, t):
        """Set current timestamp of the animation"""
        if self.playing:
            self._last_started_at = time.perf_counter() - t
        else:
            self._last_timestamp = t

    def is_playing(self):
        """Get the playing status of the timeline"""
        return self.playing

    def is_stopped(self):
        """Get the stopped status of the timeline"""
        return not self.playing and not self._last_timestamp

    def is_paused(self):
        """Get the paused status of the timeline"""
        return not self.playing and self._last_timestamp

    def set_speed(self, speed):
        """Set the speed of the timeline"""
        self.speed = speed

    def get_speed(self):
        """Get the speed of the timeline"""
        return self.speed

    def translate(self, timestamp, position, pre_cp=None, post_cp=None):
        self.set_keyframe('position', timestamp, position, pre_cp, post_cp)

    def rotate(self, timestamp, quat):
        pass

    def scale(self, timestamp, scalar):
        self.set_keyframe('scale', timestamp, scalar)

    def set_color(self, timestamp, color):
        self.set_keyframe('color', timestamp, color)

    def set_keyframes(self, timestamp, keyframes):
        for key in keyframes:
            self.set_keyframe(key, timestamp, keyframes[key])

    def set_keyframe(self, attrib, timestamp, value, pre_cp=None,
                     post_cp=None):
        if attrib not in self._keyframes:
            self._keyframes[attrib] = {}
            self._pre_cps[attrib] = {}
            self._post_cps[attrib] = {}
            self._interpolators[attrib] = LinearInterpolator({})

        self._keyframes[attrib][timestamp] = value.astype(np.float)
        self._pre_cps[attrib][timestamp] = pre_cp
        self._post_cps[attrib][timestamp] = post_cp

        if attrib not in self._interpolators:
            self._interpolators[attrib] = LinearInterpolator(
                self._keyframes[attrib])
        else:
            self._interpolators[attrib].setup()

    def get_custom_data(self, timestamp):
        pass

    def set_interpolator(self, attrib, interpolator):
        if attrib in self._keyframes:
            if interpolator is BezierInterpolator:
                self._interpolators[attrib] = interpolator(
                    self._keyframes[attrib], self._pre_cps[attrib],
                    self._post_cps[attrib])
            else:
                self._interpolators[attrib] = interpolator(
                    self._keyframes[attrib])

    def set_position_interpolator(self, interpolator):
        self.set_interpolator('position', interpolator)

    def set_scale_interpolator(self, interpolator):
        self.set_interpolator('scale', interpolator)

    def set_color_interpolator(self, interpolator):
        self.set_interpolator('color', interpolator)

    def get_position(self, t=None):
        return self._interpolators['position'].interpolate(t)

    def get_quaternion(self, t=None):
        return self._interpolators['rotation'].interpolate(t)

    def get_scale(self, t=None):
        return self._interpolators['scale'].interpolate(t)

    def get_color(self, t=None):
        return self._interpolators['color'].interpolate(t or
                                                        self.get_current_timestamp())

    def get_custom_attrib(self, attrib, t):
        return self._interpolators[attrib].interpolate(t)

    def add_actor(self, actor):
        if self._is_using_shaders:
            self._use_shader(actor)
        self._actors.append(actor)

    def get_actors(self):
        return self._actors

    def remove_actor(self, actor):
        self._actors.remove(actor)

    def update(self, t=None):
        if t is None:
            t = self.get_current_timestamp()
        self._current_timestamp = t
        if not self._is_using_shaders:
            position = self.get_position(t)
            scale = self.get_scale(t)
            col = np.clip(self.get_color(t), 0, 1) * 255
            for actor in self.get_actors():
                actor.SetPosition(*position)
                actor.SetScale(scale)

                #  heavy
                actor.vcolors[:] = col
                utils.update_actor(actor)
        else:
            for actor in self.get_actors():
                actor.GetShaderProperty().GetVertexCustomUniforms().SetUniformf(
                    'time', t)

    def seek(self, new_timestamp):
        """Change the current timestamp of the animation"""
        t = self.get_current_timestamp()
        if self.playing:
            self._last_started_at = time.perf_counter() - t
        else:
            self._last_timestamp = t
            self.update()


class CompositeTimeline:
    """One or multiple Timeline objects composer

    This composite timeline is responsible for controlling multiple key frame animation
    timelines for a better performance.
    """

    def __init__(self):
        self._timelines = []
        self._last_timestamp = 0
        self._last_started_at = 0
        self.playing = False
        self.speed = 1
        self.last_timestamp = 0
        self._current_timestamp = 0

    def _update_last_timestamp(self):
        self.last_timestamp = max(i.last_timestamp for i in self._timelines)

    def add_timeline(self, timeline: Timeline):
        self._timelines.append(timeline)
        self._update_last_timestamp()
        self._assign_current_timestamp(timeline)

    def remove_timeline(self, timeline):
        self._timelines.remove(timeline)

    def remove_timelines(self):
        self._timelines.clear()

    def get_timelines(self):
        return self._timelines

    def play(self):
        """Play the animation"""
        if not self.playing:
            self._last_started_at = time.perf_counter() - self._last_timestamp
            self.playing = True

    def pause(self):
        """Pause the animation"""
        self._last_timestamp = self.get_current_timestamp()
        self.playing = False
        self.update(force=True)

    def stop(self):
        """Stops the animation"""
        self._last_timestamp = 0
        self.playing = False
        self.update(force=True)

    def restart(self):
        """Restarts the animation"""
        self._last_timestamp = 0
        self.playing = True
        self.update(force=True)

    def get_current_timestamp(self):
        """Get current timestamp of the animation"""
        self._current_timestamp = (time.perf_counter() - self._last_started_at)\
            if self.playing else self._last_timestamp
        return self._current_timestamp

    def seek(self, t):
        """Change the current timestamp of the animation"""
        if self.playing:
            self._last_started_at = time.perf_counter() - t
        else:
            self._last_timestamp = t
            self.update(force=True)

    def is_playing(self):
        """Get the playing status of the timeline"""
        return self.playing

    def is_stopped(self):
        """Get the stopped status of the timeline"""
        return not self.playing and not self._last_timestamp

    def is_paused(self):
        """Get the paused status of the timeline"""
        return not self.playing and self._last_timestamp

    def set_speed(self, speed):
        """Set the speed of the timeline"""
        self.speed = speed

    def update(self, force=False):
        """Update the timelines"""
        if self.playing or force:
            t = self.get_current_timestamp()
            [tl.update(t) for tl in self._timelines]
