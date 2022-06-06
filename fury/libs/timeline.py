from time import sleep

import numpy as np
from scipy.interpolate import interp1d, interp2d, interpolate

from fury.libs.interpolation import *
from fury.libs.keyframe import *


class Timeline(object):
    def __init__(self, duration_ms, fps, initial_keyframe, interpolation_method: int):
        super(Timeline, self).__init__()
        self.keyframes = {}
        self.timestamps = np.array([])
        self.length = duration_ms
        self.lastKeyframe = initial_keyframe
        self.fps = fps
        self.init_keyframe(initial_keyframe)
        self._interpolation_method = interpolation_method
        self.last_value = initial_keyframe.key
        # for visualizing footsteps and control points
        self.footsteps = []

    def init_keyframe(self, initial_keyframe):
        self.timestamps = np.append(self.timestamps, initial_keyframe.timestamp)
        self.keyframes[initial_keyframe.timestamp] = initial_keyframe.key

    def getKeyframesCount(self):
        return len(self.keyframes)
    
    def get_footsteps(self):
        return self.footsteps

    def add_footsteps(self, point):
        self.footsteps.append(point)

    def clear_footsteps(self):
        self.footsteps = []


class TranslateTimeline(Timeline):
    def __init__(self, duration_ms, fps, initial_keyframe=Keyframe(0, np.array([0, 0, 0])), method=LINEAR):
        super(TranslateTimeline, self).__init__(duration_ms, fps, initial_keyframe, method)
        # used to sync cubic interpolation with the original keyframe timestamps
        self.linear_lengths = []

    def addKeyframe(self, keyframe):
        self.keyframes[keyframe.timestamp] = keyframe.key
        self.timestamps = np.array(sorted(self.keyframes.keys()))

        # sorted by timestamps
        points = [self.keyframes[i] for i in sorted(self.keyframes.keys())]

        self.linear_lengths = []
        for x, y in zip(points, points[1:]):
            self.linear_lengths.append(math.sqrt((x[1] - y[1]) * (x[1] - y[1]) + (x[0] - y[0]) * (x[0] - y[0])))

    def get_pos(self, t_ms):
        try:
            start_time = self.timestamps[self.timestamps <= t_ms].max()
        except:
            return self.get_control_points()[0]
        try:
            end_time = self.timestamps[self.timestamps > t_ms].min()
        except:
            return self.get_control_points()[-1]

        # linear interpolation
        if self._interpolation_method == LINEAR:
            p1 = self.keyframes[start_time]
            p2 = self.keyframes[end_time]
            self.last_value = linear_interpolate(p1, p2, start_time, end_time, t_ms)
            return self.last_value

        # nonlinear interpolation
        else:
            mi_index = np.where(self.timestamps == start_time)[0][0]
            dt = (t_ms - start_time) / (end_time - start_time)
            control_points = self.get_control_points()

            if self._interpolation_method == CUBIC_BEZIER:
                # all periods are equal in segments
                t = (mi_index + dt) / (len(self.timestamps) - 1)
                self.last_value = cubic_bezier_interpolate(control_points, t)
                return self.last_value

            elif self._interpolation_method == B_SPLINE:
                t = (mi_index + dt) / (len(self.timestamps) - 1)
                self.last_value = b_spline_interpolate(control_points, t)
                return self.last_value

            elif self._interpolation_method == CUBIC_SPLINE:
                # all periods are equal in segments
                sect = sum(self.linear_lengths[:mi_index])
                t = (sect + dt * (self.linear_lengths[mi_index])) / sum(self.linear_lengths)
                self.last_value = cubic_spline_interpolate(control_points, t)
                return self.last_value

    def get_interpolation_method(self):
        return self._interpolation_method

    def set_interpolation_method(self, method):
        self._interpolation_method = method

    def get_control_points(self):
        return [self.keyframes[i] for i in sorted(self.keyframes.keys())]


class ScaleTimeline(Timeline):
    def __init__(self, duration_ms, fps, initial_keyframe=Keyframe(0, np.array([1, 1, 1])), method=LINEAR):
        super(ScaleTimeline, self).__init__(duration_ms, fps, initial_keyframe, method)

    def addKeyframe(self, keyframe):
        self.keyframes[keyframe.timestamp] = keyframe.key
        self.timestamps = np.array(sorted(self.keyframes.keys()))

    def get_scale(self, t_ms):
        try:
            start_time = self.timestamps[self.timestamps <= t_ms].max()
        except:
            return self.last_value
        try:
            end_time = self.timestamps[self.timestamps > t_ms].min()
        except:
            return self.last_value

        # linear interpolation
        if self._interpolation_method == LINEAR:
            p1 = self.keyframes[start_time]
            p2 = self.keyframes[end_time]
            self.last_value = linear_interpolate(p1, p2, start_time, end_time, t_ms)
            # self.add_footsteps(self.last_value)
            return self.last_value

    def get_keyframes(self):
        return [self.keyframes[i] for i in sorted(self.keyframes.keys())]


class ColorTimeline(Timeline):
    def __init__(self, duration_ms, fps, initial_keyframe=Keyframe(0, np.array([255, 255, 255])), method=LINEAR):
        super(ColorTimeline, self).__init__(duration_ms, fps, initial_keyframe, method)

    def addKeyframe(self, keyframe):
        self.keyframes[keyframe.timestamp] = keyframe.key
        self.timestamps = np.array(sorted(self.keyframes.keys()))

    def get_color(self, t_ms):
        try:
            start_time = self.timestamps[self.timestamps <= t_ms].max()
        except:
            return self.last_value
        try:
            end_time = self.timestamps[self.timestamps > t_ms].min()
        except:
            return self.last_value

        # linear interpolation
        if self._interpolation_method == LINEAR:
            p1 = self.keyframes[start_time]
            p2 = self.keyframes[end_time]
            self.last_value = linear_interpolate(p1, p2, start_time, end_time, t_ms)
            # self.add_footsteps(self.last_value)
            return self.last_value
