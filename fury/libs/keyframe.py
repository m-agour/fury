import numpy as np


class Keyframe(object):
    def __init__(self, timestamp: float, key):
        self.timestamp = timestamp
        self.key = np.array(key)

    def get_timestamp(self):
        return self.timestamp

    def get_key(self):
        return self.key
