import math
import time
import numpy as np

from fury import actor


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
            return self.timestamps[0]

    def _get_nearest_larger_timestamp(self, t):
        try:
            return self.timestamps[self.timestamps > t].min()
        except:
            return self.timestamps[-1]


class StepInterpolator(Interpolator):
    def __init__(self, keyframes):
        super(StepInterpolator, self).__init__(keyframes)

    def interpolate(self, t):
        t_lower = self._get_nearest_smaller_timestamp(t)
        return self.keyframes[t_lower]


class LinearInterpolator(Interpolator):
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


class Timeline:
    def __init__(self, actors):
        self._keyframes = {}
        self._keyframes = {'position': {}, 'rotation': {}, 'scale': {}, 'color': {}}
        self._interpolators = self._init_interpolators()
        self._actors = actors

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
        return (time.perf_counter() - self._last_started_at) if self.playing else self._last_timestamp

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
        pass

    def get_interpolator(self, attrib):
        pass

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
        color = self.get_color(t)
        for actor in self.get_actors():
            actor.SetPosition(position)
            actor.SetScale(scale)
            actor.GetProperty().SetColor(1, 0, 0)


