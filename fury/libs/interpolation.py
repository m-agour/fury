import math
import numpy as np
from scipy import interpolate

LINEAR = 1
CUBIC_BEZIER = 2
B_SPLINE = 3
CUBIC_SPLINE = 4

interpolation_methods = {LINEAR: 'Linear',
                         CUBIC_BEZIER: 'Bezier',
                         B_SPLINE: 'B-Spline',
                         CUBIC_SPLINE: 'Cubic Spline'}


def linear_interpolate(p1, p2, t1, t2, t):
    d = p2 - p1
    dt = (t - t1) / (t2 - t1)
    return dt * d + p1


def cubic_bezier_interpolate(points, t):
    point = np.array([0.0, 0.0, 0.0])
    n = len(points) - 1
    for k in range(n + 1):
        constant = math.comb(n, k) * (t ** k) * ((1 - t) ** (n - k))
        point += points[k] * constant
    return point


def b_spline_interpolate(points, t, degree=2):
    n = len(points)
    t *= n - degree
    points = np.asarray(points)
    degree = np.clip(degree, 1, n - 1)
    kv = np.concatenate(([0] * degree, np.arange(n - degree + 1), [n - degree] * degree))
    return np.array(interpolate.splev(t, (kv, points.T, degree))).T


def cubic_spline_interpolate(points, t, smoothness=3):
    points = np.asarray(points)
    tck, u = interpolate.splprep(points.T, s=smoothness)
    return np.array(interpolate.splev(t, tck))
