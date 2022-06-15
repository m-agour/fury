import math
import time
import numpy as np


class Interpolator(object):
    def __init__(self, keyframes):
        super(Interpolator, self).__init__()
        self.keyframes = keyframes
        self.timestamps = {
            key: np.sort(np.array(list(keyframes[key].keys())), axis=None)
            for key, value in keyframes.items()}

    def _get_nearest_smaller_timestamp(self, t, typ):
        try:
            return self.timestamps[typ][self.timestamps[typ] <= t].max()
        except:
            return self.timestamps[typ][0]

    def _get_nearest_larger_timestamp(self, t, typ):
        try:
            return self.timestamps[typ][self.timestamps[typ] > t].min()
        except:
            return self.timestamps[typ][-1]


class StepInterpolator(Interpolator):
    def __init__(self, keyframes):
        super(StepInterpolator, self).__init__(keyframes)

    def interpolate(self, t, typ):
        t_lower = self._get_nearest_smaller_timestamp(t, typ)
        return self.keyframes[typ][t_lower]


class LinearInterpolator(Interpolator):
    def __init__(self, keyframes):
        super(LinearInterpolator, self).__init__(keyframes)

    def interpolate(self, t, typ):
        t1 = self._get_nearest_smaller_timestamp(t, typ)
        t2 = self._get_nearest_larger_timestamp(t, typ)
        if t1 == t2:
            return self.keyframes[typ][t1]
        p1 = self.keyframes[typ][t1]
        p2 = self.keyframes[typ][t2]
        d = p2 - p1
        dt = (t - t1) / (t2 - t1)
        return dt * d + p1


class Timeline:
    def __init__(self, keyframes, interpolator, actors):
        self._in_time = 0
        self._out_time = math.inf
        self._keyframes = keyframes
        self._actors = actors
        self.interpolator = interpolator(keyframes)

        self.playing = False
        self.loop = False
        self.reversePlaying = False
        self._last_started_at = 0
        self._last_timestamp = 0
        self.speed = 1

    def add_actor(self, actor):
        self._actors.append(actor)

    def remove_actor(self, actor):
        self._actors.remove(actor)

    def play(self):
        self._last_started_at = time.perf_counter() - self._last_timestamp
        self.playing = True

    def pause(self):
        self._last_timestamp = self.current_timestamp()
        self.playing = False

    def stop(self):
        self._last_timestamp = 0
        self.playing = False

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


data = {'position': {1: np.array([1, 2, 3]), 2: np.array([11, 2, 0]), 3: np.array([0, 0, 0])}}

tl1 = Timeline(data, LinearInterpolator, [])
tl2 = Timeline(data, StepInterpolator, [])
