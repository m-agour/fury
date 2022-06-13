import numpy as np
import numpy.testing as npt
from fury.animation import Timeline, LinearInterpolator, StepInterpolator


def test_step_interpolator():
    data = {'position': {1: np.array([1, 2, 3]), 2: np.array([11, 2, 0]), 3: np.array([0, 0, 0])}}
    interpolator = StepInterpolator(data)

    pos1 = interpolator.interpolate(2, 'position')
    pos2 = interpolator.interpolate(2.9, 'position')
    npt.assert_equal(pos1, pos2)

    pos3 = interpolator.interpolate(3, 'position')
    npt.assert_equal(np.any(np.not_equal(pos3, pos2)), True)

    pos_initial = interpolator.interpolate(1, 'position')
    pos_final = interpolator.interpolate(3, 'position')
    npt.assert_equal(interpolator.interpolate(0, 'position'), pos_initial)
    npt.assert_equal(interpolator.interpolate(999, 'position'), pos_final)

    for t in range(-10, 40, 1):
        interpolator.interpolate(t/10, 'position')


def test_linear_interpolator():
    data = {'position': {1: np.array([1, 2, 3]), 2: np.array([11, 2, 0]), 3: np.array([0, 0, 0])}}
    interpolator = LinearInterpolator(data)

    pos1 = interpolator.interpolate(2, 'position')
    pos2 = interpolator.interpolate(2.1, 'position')
    npt.assert_equal(np.any(np.not_equal(pos1, pos2)), True)
    npt.assert_equal(pos1, np.array([11, 2, 0]))

    for t in range(-10, 40, 1):
        interpolator.interpolate(t/10, 'position')

