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

