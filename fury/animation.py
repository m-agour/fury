import time
import numpy as np
from fury.colormap import _rgb2lab, _lab2rgb

from fury import utils


class Keyframe:
    def __init__(self, timestamp, value):
        self.timestamp = timestamp
        self.value = value


class Interpolator(object):
    def __init__(self, keyframes):
        super(Interpolator, self).__init__()
        self.keyframes = keyframes
        self.timestamps = np.sort(np.array(list(keyframes)), axis=None)

    def update_timestamps(self):
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


class StepInterpolator(Interpolator):
    def __init__(self, keyframes):
        super(StepInterpolator, self).__init__(keyframes)

    def interpolate(self, t):
        t_lower = self._get_nearest_smaller_timestamp(t)
        return self.keyframes[t_lower]


class LinearInterpolator(Interpolator):
    """Linear interpolator for keyframes.

    This is a general linear interpolator to be used for any shape of keyframes data.
    """
    def __init__(self, keyframes):
        super(LinearInterpolator, self).__init__(keyframes)

    def interpolate(self, t):
        t1 = self._get_nearest_smaller_timestamp(t)
        t2 = self._get_nearest_larger_timestamp(t)
        if t1 == t2:
            return self.keyframes[t1]
        p1 = self.keyframes[t1]
        p2 = self.keyframes[t2]
        d = p2 - p1
        dt = (t - t1) / (t2 - t1)
        return dt * d + p1


class LABInterpolator(Interpolator):
    """LAB interpolator for color keyframes """

    def __init__(self, keyframes):
        super(LABInterpolator, self).__init__(keyframes)
        self.lab_keyframes = self._initialize_lab_keyframes()

    def _initialize_lab_keyframes(self):
        lab_keyframes = {}
        for key, value in self.keyframes.items():
            lab_keyframes[key] = _rgb2lab(np.array([value]))
        return lab_keyframes

    def interpolate(self, t):
        t1 = self._get_nearest_smaller_timestamp(t)
        t2 = self._get_nearest_larger_timestamp(t)
        if t1 == t2:
            return self.keyframes[t1]
        p1 = self.lab_keyframes[t1]
        p2 = self.lab_keyframes[t2]
        d = p2 - p1
        dt = (t - t1) / (t2 - t1)
        return _lab2rgb(dt * d + p1)

class Timeline:
    """Keyframe animation timeline class.

    This timeline is responsible for keyframe animations for a single or a group of models.
    It's used to handle multiple attributes and properties of Fury actors such as transformations, color, and scale.
    It also accepts custom data and interpolates them such as temperature.
    Linear interpolation is used by default to interpolate data between main keyframes.
    """
    def __init__(self, actors=None):
        self._keyframes = {}
        self._keyframes = {'position': {0: np.array([0, 0, 0])}, 'rotation': {0: np.array([0, 0, 0])},
                           'scale': {0: np.array([0, 0, 0])}, 'color': {0: np.array([0, 0, 0])}}
        self._interpolators = self._init_interpolators()

        # Handle actors while constructing the timeline.
        if actors is not None:
            if isinstance(actors, list):
                self._actors = actors.copy()
            else:
                self._actors = [actors]

        self.playing = False
        self.loop = False
        self.reversePlaying = False
        self._last_started_at = 0
        self._last_timestamp = 0
        self.speed = 1

    def _init_interpolators(self):
        return {'position': LinearInterpolator(self._keyframes["position"]),
                'rotation': LinearInterpolator(self._keyframes["rotation"]),
                'scale': LinearInterpolator(self._keyframes["scale"]),
                'color': LinearInterpolator(self._keyframes["color"])}

    def play(self):
        if not self.playing:
            self._last_started_at = time.perf_counter() - self._last_timestamp
            self.playing = True

    def pause(self):
        self._last_timestamp = self.current_timestamp
        self.playing = False

    def stop(self):
        self._last_timestamp = 0
        self.playing = False

    @property
    def current_timestamp(self):
        """Get current timestamp of the animation"""
        return (time.perf_counter() - self._last_started_at) if self.playing else self._last_timestamp

    @property
    def last_timestamp(self):
        """Get the max timestamp of all keyframes"""
        return max(list(max(list(self._keyframes[i].keys()) for i in self._keyframes.keys())))

    def set_timestamp(self, t):
        """Set current timestamp of the animation"""
        if self.playing:
            self._last_started_at = time.perf_counter() - t
        else:
            self._last_timestamp = t

    def is_playing(self):
        return self.playing

    def is_stopped(self):
        return not self.playing and not self._last_timestamp

    def is_paused(self):
        return not self.playing and self._last_timestamp

    def set_speed(self, speed):
        self.speed = speed

    def get_speed(self):
        return self.speed

    def translate(self, timestamp, position):
        self.set_custom_data('position', timestamp, position)

    def rotate(self, timestamp, quat):
        pass

    def scale(self, timestamp, scalar):
        self.set_custom_data('scale', timestamp, scalar)

    def set_color(self, timestamp, color):
        self.set_custom_data('color', timestamp, color)

    def set_keyframes(self, timestamp, keyframes):
        for key in keyframes:
            self.set_custom_data(key, timestamp, keyframes[key])

    def set_custom_data(self, attrib, timestamp, value):
        if attrib not in self._keyframes:
            self._keyframes[attrib] = {}
            self._interpolators[attrib] = LinearInterpolator({})

        self._keyframes[attrib][timestamp] = value

        if attrib not in self._interpolators:
            self._interpolators[attrib] = LinearInterpolator(self._keyframes[attrib])
        self._interpolators[attrib].update_timestamps()

    def get_custom_data(self, timestamp):
        pass

    def set_interpolator(self, attrib, interpolator):
        if attrib in self._keyframes:
            self._interpolators[attrib] = interpolator(self._keyframes[attrib])

    def set_position_interpolator(self, interpolator):
        self.set_interpolator('position', interpolator)

    def set_scale_interpolator(self, interpolator):
        self.set_interpolator('scale', interpolator)

    def set_color_interpolator(self, interpolator):
        self.set_interpolator('color', interpolator)

    def get_position(self, t):
        return self._interpolators['position'].interpolate(t)

    def get_quaternion(self, t):
        return self._interpolators['rotation'].interpolate(t)

    def get_scale(self, t):
        return self._interpolators['scale'].interpolate(t)

    def get_color(self, t):
        return self._interpolators['color'].interpolate(t)

    def get_custom_attrib(self, attrib, t):
        return self._interpolators[attrib].interpolate(t)

    def add_actor(self, actor):
        self._actors.append(actor)

    def get_actors(self):
        return self._actors

    def remove_actor(self, actor):
        self._actors.remove(actor)

    def update(self):
        t = self.current_timestamp
        position = self.get_position(t)
        scale = self.get_scale(t)
        color = self.get_color(t) * 255

        for actor in self.get_actors():
            actor.SetPosition(position)
            actor.SetScale(scale)

            vcolors = utils.colors_from_actor(actor)
            vcolors[:] = color
            utils.update_actor(actor)



