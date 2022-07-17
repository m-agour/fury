import math
import time
import numpy as np
from scipy import interpolate
from scipy.spatial import transform
from fury import utils
from fury.actor import Container
from fury.colormap import rgb2hsv, hsv2rgb, rgb2lab, lab2rgb, xyz2rgb, rgb2xyz
from fury.ui.elements import PlaybackPanel
from vtkmodules.vtkRenderingCore import vtkActor


class Interpolator(object):
    def __init__(self, keyframes):
        super(Interpolator, self).__init__()
        self.keyframes = keyframes
        self.timestamps = []
        self.min_timestamp = 0
        self.final_timestamp = 0
        self._unity_kf = True
        self.setup()

    def setup(self):
        self.timestamps = np.sort(np.array(list(self.keyframes)), axis=None)
        self.min_timestamp = self.timestamps[0]
        self.final_timestamp = self.timestamps[-1]
        if len(self.timestamps) == 1:
            self._unity_kf = True
        else:
            self._unity_kf = False

    def _get_nearest_smaller_timestamp(self, t, include_last=False):
        if t > self.min_timestamp:
            if include_last:
                return self.timestamps[self.timestamps <= t].max()
            return self.timestamps[:-1][self.timestamps[:-1] <= t].max()
        return self.min_timestamp

    def _get_nearest_larger_timestamp(self, t, include_first=False):
        if t < self.final_timestamp:
            if include_first:
                return self.timestamps[self.timestamps > t].min()
            return self.timestamps[1:][self.timestamps[1:] > t].min()
        return self.timestamps[-1]

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
            k1 = {"t": t_s, "data": self.keyframes[t_s]['value']}
            k2 = {"t": t_e, "data": self.keyframes[t_e]['value']}
        if isinstance(self, CubicBezierInterpolator):
            k1["cp"] = self.keyframes['post_cp'][t_s]
            k2["cp"] = self.keyframes['pre_cp'][t_e]
        return {"start": k1, "end": k2}

    @staticmethod
    def _lerp(v1, v2, t1, t2, t):
        if t1 == t2:
            return v1
        v = v2 - v1
        dt = 0 if t <= t1 else 1 if t >= t2 else (t - t1) / (t2 - t1)
        return dt * v + v1

    @staticmethod
    def _get_time_delta(t, t1, t2):
        return 0 if t <= t1 else 1 if t >= t2 else (t - t1) / (t2 - t1)

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
        t_lower = self._get_nearest_smaller_timestamp(t, include_last=True)
        return self.keyframes.get(t_lower).get('value')


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

    def interpolate(self, t):
        if self._unity_kf:
            t = self.timestamps[0]
            return self.keyframes.get(t).get('value')
        t1 = self._get_nearest_smaller_timestamp(t)
        t2 = self._get_nearest_larger_timestamp(t)
        p1 = self.keyframes.get(t1).get('value')
        p2 = self.keyframes.get(t2).get('value')
        return self._lerp(p1, p2, t1, t2, t)


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
        points = np.asarray([self.keyframes.get(t).get('value') for t in
                             self.timestamps])

        if len(points) < (self.degree + 1):
            raise ValueError(f"Minimum {self.degree + 1} "
                             f"keyframes must be set in order to use "
                             f"{self.degree}-degree spline")

        self.tck = interpolate.splprep(points.T, k=self.degree, full_output=1,
                                       s=self.smoothness)[0][0]
        self.linear_lengths = []
        for x, y in zip(points, points[1:]):
            self.linear_lengths.append(np.linalg.norm(x - y))

    def interpolate(self, t):

        t1 = self._get_nearest_smaller_timestamp(t)
        t2 = self._get_nearest_larger_timestamp(t)

        mi_index = np.where(self.timestamps == t1)[0][0]
        dt = self._get_time_delta(t, t1, t2)
        sect = sum(self.linear_lengths[:mi_index])
        ts = (sect + dt * (self.linear_lengths[mi_index])) / sum(
            self.linear_lengths)
        return np.array(interpolate.splev(ts, self.tck))


class CubicSplineInterpolator(SplineInterpolator):
    """Cubic spline interpolator for keyframes.

    This is a general cubic spline interpolator to be used for any shape of
    keyframes data.
    """

    def __init__(self, keyframes, smoothness=3):
        super(CubicSplineInterpolator, self).__init__(keyframes, degree=3,
                                                      smoothness=smoothness)
        self.id = 7


class CubicBezierInterpolator(Interpolator):
    """Cubic bezier interpolator for keyframes.

    This is a general cubic bezier interpolator to be used for any shape of
    keyframes data.

    Attributes
    ----------
    keyframes : dict
        Keyframes to be interpolated at any time.

    Notes
    -----
    If no control points are set in the keyframes, The cubic
    Bezier interpolator will almost as the linear interpolator
    """

    def __init__(self, keyframes):
        super(CubicBezierInterpolator, self).__init__(keyframes)
        self.id = 2

    def setup(self):
        super(CubicBezierInterpolator, self).setup()
        for ts in self.timestamps:
            # keyframe at timestamp
            kf_ts = self.keyframes.get(ts)
            if 'pre_cp' not in kf_ts or kf_ts.get('pre_cp') is None:
                kf_ts['pre_cp'] = self.keyframes.get(ts).get('value')
            if 'post_cp' not in kf_ts or kf_ts.get('post_cp') is None:
                kf_ts['post_cp'] = self.keyframes.get(ts).get('value')

    def interpolate(self, t):
        t1, t2 = self.get_neighbour_timestamps(t)
        p0 = self.keyframes.get(t1).get('value')
        p1 = self.keyframes.get(t1).get('post_cp')
        p2 = self.keyframes.get(t2).get('pre_cp')
        p3 = self.keyframes.get(t2).get('value')
        dt = self._get_time_delta(t, t1, t2)
        res = (1 - dt) ** 3 * p0 + 3 * (1 - dt) ** 2 * dt * p1 + 3 * \
              (1 - dt) * dt ** 2 * p2 + dt ** 3 * p3
        return res


class Slerp(Interpolator):
    """Spherical based rotation keyframes interpolator.

    A rotation interpolator to be used for rotation keyframes.

    Attributes
    ----------
    keyframes : dict
        Rotation keyframes to be interpolated at any time.
    """

    def __init__(self, keyframes):
        self._slerp = None
        super(Slerp, self).__init__(keyframes)

    def setup(self):
        super(Slerp, self).setup()
        timestamps, euler_rots = [], []
        for ts in self.keyframes:
            timestamps.append(ts)
            euler_rots.append(self.keyframes.get(ts).get('value'))
        rotations = transform.Rotation.from_euler('xyz', euler_rots,
                                                  degrees=True)
        self._slerp = transform.Slerp(timestamps, rotations)

    @staticmethod
    def _quaternion2euler(x, y, z, w):
        ysqr = y * y

        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + ysqr)
        X = np.degrees(np.arctan2(t0, t1))

        t2 = +2.0 * (w * y - z * x)

        t2 = np.clip(t2, a_min=-1.0, a_max=1.0)
        Y = np.degrees(np.arcsin(t2))

        t3 = 2.0 * (w * z + x * y)
        t4 = 1.0 - 2.0 * (ysqr + z * z)
        Z = np.degrees(np.arctan2(t3, t4))

        return X, Y, Z

    def interpolate(self, t):
        min_t = self.timestamps[0]
        max_t = self.timestamps[-1]
        t = min_t if t < min_t else max_t if t > max_t else t
        v = self._slerp(t)
        q = v.as_quat()
        return self._quaternion2euler(*q)


class ColorInterpolator(Interpolator):
    """Color keyframes interpolator.

    A color interpolator to be used for color keyframes.
    Given two functions, one to convert from rgb space to the interpolation
    space, the other is to
    Attributes
    ----------
    keyframes : dict
        Keyframes to be interpolated at any time.

    Notes
    -----
    If no control points are set in the keyframes, The cubic
    Bezier interpolator will almost as the linear interpolator
    """

    def __init__(self, keyframes, rgb_to_space, space_to_rgb):
        self.rgb_to_space = rgb_to_space
        self.space_to_rgb = space_to_rgb
        self.space_keyframes = {}
        super(ColorInterpolator, self).__init__(keyframes)

    def setup(self):
        super(ColorInterpolator, self).setup()
        for ts, keyframe in self.keyframes.items():
            self.space_keyframes[ts] = self.rgb_to_space(keyframe.get('value'))

    def interpolate(self, t):
        t1, t2 = self.get_neighbour_timestamps(t)
        p1 = self.space_keyframes.get(t1)
        p2 = self.space_keyframes.get(t2)
        lab_val = self._lerp(p1, p2, t1, t2, t)
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


class Timeline(Container):
    """Keyframe animation timeline class.

    This timeline is responsible for keyframe animations for a single or a
    group of models.
    It's used to handle multiple attributes and properties of Fury actors such
    as transformations, color, and scale.
    It also accepts custom data and interpolates them such as temperature.
    Linear interpolation is used by default to interpolate data between main
    keyframes.
    """

    def __init__(self, actors=None, playback_panel=False):
        super().__init__()
        self._data = {
            'keyframes': {
                'attribs': {},
                'camera': {}
            },
            'interpolators': {
                'attribs': {},
                'camera': {}
            }
        }
        self.loop = False
        self.reversePlaying = False
        self._last_started_at = 0
        self._last_timestamp = 0
        self._current_timestamp = 0
        self.speed = 1
        self._timelines = []
        self._camera = None
        self._scene = None
        self._last_timestamp = 0
        self._last_started_at = 0
        self._playing = False
        self.speed = 2
        self._current_timestamp = 0
        self._has_playback_panel = playback_panel
        self._final_timestamp = 0

        # Handle actors while constructing the timeline.
        if playback_panel:
            self.playback_panel = PlaybackPanel()
            self.playback_panel.on_play_button_clicked = self.play
            self.playback_panel.on_stop_button_clicked = self.stop
            self.playback_panel.on_pause_button_clicked = self.pause
            self.playback_panel.on_progress_bar_changed = self.seek

        if actors is not None:
            self.add_actor(actors)

    def update_final_timestamp(self):
        """Calculate and Get the final timestamp of all keyframes.

        Returns
        -------
        float
            final timestamp that can be reached inside the Timeline.
        """

        self._final_timestamp = max(self._final_timestamp,
                                    max([0] + [tl.update_final_timestamp() for
                                               tl in self._timelines]))
        if self._has_playback_panel:
            self.playback_panel.final_time = self._final_timestamp
        return self._final_timestamp

    def set_timestamp(self, timestamp):
        """Set current timestamp of the animation.

        Parameters
        ----------
        timestamp: float
            Current timestamp to be set.
        """
        if self.playing:
            self._last_started_at = time.perf_counter() - timestamp
        else:
            self._last_timestamp = timestamp

    def set_keyframe(self, attrib, timestamp, value, pre_cp=None,
                     post_cp=None, is_camera=False):
        """Set a keyframe for a certain property.

        Parameters
        ----------
        attrib: str
            The name of the attribute.
        timestamp: float
            Timestamp of the keyframe.
        value: float
            Value of the keyframe at the given timestamp.
        is_camera: bool
            Indicated whether setting a camera property or general property.
        pre_cp: float
            The control point in case of using `cubic Bezier interpolator` when
            time exceeds this timestamp.
        post_cp: float
            The control point in case of using `cubic Bezier interpolator` when
            time precedes this timestamp.
        """
        typ = 'attribs'
        if is_camera:
            typ = 'camera'
            self._camera = self._scene.camera()

        keyframes = self._data.get('keyframes')
        if attrib not in keyframes.get(typ):
            keyframes.get(typ)[attrib] = {}
        attrib_keyframes = self._data.get('keyframes').get(typ).get(attrib)
        attrib_keyframes[timestamp] = {
            'value': np.array(value).astype(np.float),
            'pre_cp': np.array(pre_cp).astype(np.float),
            'post_cp': np.array(post_cp).astype(np.float)
        }
        interpolators = self._data.get('interpolators')
        if attrib not in interpolators.get(typ):
            interpolators.get(typ)[attrib] = \
                LinearInterpolator(attrib_keyframes)

        else:
            interpolators.get(typ).get(attrib).setup()

        if timestamp > self._final_timestamp:
            self._final_timestamp = timestamp
            if self._has_playback_panel:
                final_t = self.update_final_timestamp()
                self.playback_panel.final_time = final_t

    def set_keyframes(self, attrib, keyframes, is_camera=False):
        """Set multiple keyframes for a certain property.

        Parameters
        ----------
        attrib: str
            The name of the property.
        keyframes: dict
            A dict object containing keyframes to be set.
        is_camera: bool
            Indicated whether setting a camera property or general property.

        Notes
        ---------
        Cubic Bezier control points are not supported yet in this setter.

        Examples
        ---------
        >>> pos_keyframes = {1: np.array([1, 2, 3]), 3: np.array([5, 5, 5])}
        >>> Timeline.set_keyframes('position', pos_keyframes)
        """
        for t in keyframes:
            keyframe = keyframes.get(t)
            self.set_keyframe(attrib, t, keyframe, is_camera=is_camera)

    def set_camera_keyframe(self, attrib, timestamp, value, pre_cp=None,
                            post_cp=None):
        """Set a keyframe for a camera property

        Parameters
        ----------
        attrib: str
            The name of the attribute.
        timestamp: float
            Timestamp of the keyframe.
        value: float
            Value of the keyframe at the given timestamp.
        pre_cp: float
            The control point in case of using `cubic Bezier interpolator` when
            time exceeds this timestamp.
        post_cp: float
            The control point in case of using `cubic Bezier interpolator` when
            time precedes this timestamp.
        """
        self.set_keyframe(attrib, timestamp, value, pre_cp, post_cp, True)

    def set_camera_keyframes(self, attrib, keyframes):
        """Set multiple keyframes for a certain camera property

        Parameters
        ----------
        attrib: str
            The name of the property.
        keyframes: dict
            A dict object containing keyframes to be set.

        Notes
        ---------
        Cubic Bezier control points are not supported yet in this setter.

        Examples
        ---------
        >>> cam_pos = {1: np.array([1, 2, 3]), 3: np.array([5, 5, 5])}
        >>> Timeline.set_camera_keyframes('position', cam_pos)
        """
        self.set_keyframes(attrib, keyframes, is_camera=True)

    def set_interpolator(self, attrib, interpolator, is_camera=False,
                         spline_degree=2):
        """Set keyframes interpolator for a certain property

        Parameters
        ----------
        attrib: str
            The name of the property.
        interpolator: class
            The interpolator to be used to interpolate keyframes.
        is_camera: bool, optional
            Indicated whether dealing with a camera property or general
            property.
        spline_degree: int, optional
            The degree of the spline in case of setting a spline interpolator.

        Examples
        ---------
        >>> Timeline.set_interpolator('position', LinearInterpolator)
        """
        typ = 'attribs'
        if is_camera:
            typ = 'camera'
        if attrib in self._data.get('keyframes').get(typ):
            keyframes = self._data.get('keyframes').get(typ).get(attrib)
            self._data.get('interpolators').get(typ)[attrib] = \
                interpolator(keyframes)

    def is_interpolatable(self, attrib, is_camera=False):
        """Checks if a property is interpolatable.

        Parameters
        ----------
        attrib: str
            The name of the property.
        is_camera: bool
            Indicated whether checking a camera property or general property.

        Returns
        -------
        bool
            Interpolatable state.

        Notes
        -------
        True means that it's safe to use interpolator.interpolate(t) for the
        specified property. And False means the opposite.

        Examples
        ---------
        >>> Timeline.set_interpolator('position', LinearInterpolator)
        """
        typ = 'camera' if is_camera else 'attribs'
        return attrib in self._data.get('interpolators').get(typ)

    def set_camera_interpolator(self, attrib, interpolator):

        self.set_interpolator(attrib, interpolator, is_camera=True)

    def set_position_interpolator(self, interpolator):
        self.set_interpolator('position', interpolator)

    def set_scale_interpolator(self, interpolator):
        self.set_interpolator('scale', interpolator)

    def set_rotation_interpolator(self, interpolator):
        self.set_interpolator('rotation', interpolator)

    def set_color_interpolator(self, interpolator):
        self.set_interpolator('color', interpolator)

    def set_opacity_interpolator(self, interpolator):
        self.set_interpolator('opacity', interpolator)

    def set_camera_position_interpolator(self, interpolator):
        self.set_camera_interpolator("position", interpolator)

    def set_camera_focal_interpolator(self, interpolator):
        self.set_camera_interpolator("focal", interpolator)

    def get_property_value(self, attrib, t):
        return self._data.get('interpolators').get('attribs').get(
            attrib).interpolate(t)

    def get_camera_property_value(self, attrib, t):
        return self._data.get('interpolators').get('camera').get(
            attrib).interpolate(t)

    def set_position(self, timestamp, position, pre_cp=None, post_cp=None):
        self.set_keyframe('position', timestamp, position, pre_cp, post_cp)

    def set_position_keyframes(self, keyframes):
        self.set_keyframes('position', keyframes)

    def set_rotation(self, timestamp, quat):
        self.set_keyframe('rotation', timestamp, quat)

    def set_scale(self, timestamp, scalar):
        self.set_keyframe('scale', timestamp, scalar)

    def set_scale_keyframes(self, keyframes):
        self.set_keyframes('scale', keyframes)

    def set_color(self, timestamp, color):
        self.set_keyframe('color', timestamp, color)

    def set_color_keyframes(self, keyframes):
        self.set_keyframes('color', keyframes)

    def set_opacity(self, timestamp, opacity):
        """Value from 0 to 1"""
        self.set_keyframe('opacity', timestamp, opacity)

    def set_opacity_keyframes(self, keyframes):
        self.set_keyframes('opacity', keyframes)

    def get_position(self, t):
        return self.get_property_value('position', t)

    def get_rotation(self, t):
        return self.get_property_value('rotation', t)

    def get_scale(self, t):
        return self.get_property_value('scale', t)

    def get_color(self, t):
        return self.get_property_value('color', t)

    def get_opacity(self, t):
        return self.get_property_value('opacity', t)

    def set_camera_position(self, timestamp, position):
        self.set_camera_keyframe('position', timestamp, position)

    def set_camera_position_keyframes(self, keyframes):
        self.set_camera_keyframes('position', keyframes)

    def set_camera_focal(self, timestamp, position):
        self.set_camera_keyframe('focal', timestamp, position)

    def set_camera_focal_keyframes(self, keyframes):
        self.set_camera_keyframes('focal', keyframes)

    def set_camera_view_up(self, timestamp, direction):
        self.set_camera_keyframe('view_up', timestamp, direction)

    def set_camera_view_up_keyframes(self, keyframes):
        self.set_camera_keyframes('view_up', keyframes)

    def get_camera_position(self, t):
        return self.get_camera_property_value('position', t)

    def get_camera_focal(self, t):
        return self.get_camera_property_value('focal', t)

    def get_camera_view_up(self, t):
        return self.get_camera_property_value('view_up', t)

    def add(self, item):
        if isinstance(item, list):
            for a in item:
                self.add(a)
            return
        elif isinstance(item, vtkActor):
            self.add_actor(item)
        elif isinstance(item, Timeline):
            self.add_timeline(item)
        else:
            raise ValueError(f"Object of type {type(item)} can't be added to "
                             f"the timeline.")

    def add_timeline(self, timeline):
        self._timelines.append(timeline)

    def add_actor(self, actor):
        if isinstance(actor, list):
            for a in actor:
                self.add_actor(a)
            return
        actor.vcolors = utils.colors_from_actor(actor)
        super(Timeline, self).add(actor)

    def get_actors(self):
        return self.items

    def get_timelines(self):
        return self._timelines

    def remove_timelines(self):
        self._timelines.clear()

    def remove_actor(self, actor):
        self._items.remove(actor)

    def remove_actors(self):
        self.clear()

    def update_animation(self, t=None, force=False):
        """Update the timelines"""
        if t is None:
            t = self.current_timestamp
            if t >= self._final_timestamp:
                self.pause()
        if self._has_playback_panel and not force and \
                t < self._final_timestamp:
            self.playback_panel.current_time = t
        if self.playing or force:
            if self.is_interpolatable('position', is_camera=True):
                cam_pos = self.get_camera_position(t)
                self._camera.SetPosition(cam_pos)

            if self.is_interpolatable('focal', is_camera=True):
                cam_foc = self.get_camera_focal(t)
                self._camera.SetFocalPoint(cam_foc)

            if self.is_interpolatable('view_up', is_camera=True):
                cam_up = self.get_camera_view_up(t)
                self._camera.SetViewUp(cam_up)

            if self.is_interpolatable('position'):
                position = self.get_position(t)
                self.SetPosition(position)

            if self.is_interpolatable('scale'):
                scale = self.get_scale(t)
                [act.SetScale(scale) for act in self.get_actors()]

            if self.is_interpolatable('opacity'):
                scale = self.get_opacity(t)
                [act.GetProperty().SetOpacity(scale) for
                 act in self.get_actors()]

            if self.is_interpolatable('rotation'):
                euler = self.get_rotation(t)
                [act.SetOrientation(euler) for
                 act in self.get_actors()]

            if self.is_interpolatable('color'):
                color = self.get_color(t)
                for act in self.get_actors():
                    act.vcolors[:] = color * 255
                    utils.update_actor(act)

        [tl.update_animation(t, force=True) for tl in self._timelines]

    def play(self):
        """Play the animation"""
        self.update_final_timestamp()
        if not self.playing:
            self._last_started_at = time.perf_counter() - self._last_timestamp
            self._playing = True

    def pause(self):
        """Pauses the animation"""
        self._last_timestamp = self.current_timestamp
        self._playing = False

    def stop(self):
        """Stops the animation"""
        self._last_timestamp = 0
        self._playing = False
        self.update_animation(force=True)

    def restart(self):
        """Restarts the animation"""
        self._last_timestamp = 0
        self._playing = True
        self.update_animation(force=True)

    @property
    def current_timestamp(self):
        """Get current timestamp of the animation"""
        if self.playing:
            self._last_timestamp = (time.perf_counter() -
                                    self._last_started_at) * 1
        return self._last_timestamp

    @current_timestamp.setter
    def current_timestamp(self, timestamp):
        """Set current timestamp of the animation"""
        self.seek(timestamp)

    @property
    def final_timestamp(self):
        """Get current timestamp of the animation"""
        return self._final_timestamp

    def seek(self, t):
        """Change the current timestamp of the animation"""
        if self.playing:
            self._last_started_at = time.perf_counter() - t
        else:
            self._last_timestamp = t
            self.update_animation(force=True)

    def seek_percent(self, p):
        """Change the current timestamp of the animation given a value from
        0 to 100
        """
        t = p * self._final_timestamp / 100
        self.seek(t)

    @property
    def playing(self):
        """Get the playing state of the timeline.

        Returns
        -------
        bool
            The playing state.
        """
        return self._playing

    @playing.setter
    def playing(self, playing):
        """Sets the playing state of the timeline.

        Parameters
        ----------
        playing: bool
            The playing state to be set.
        """
        self._playing = playing

    @property
    def stopped(self):
        """Get the playing state of the timeline.

        Returns
        -------
        bool
            The playing state.

        """
        return not self.playing and not self._last_timestamp

    @property
    def paused(self):
        """Get the paused status of the timeline"""
        return not self.playing and self._last_timestamp is not None

    def set_speed(self, speed):
        """Set the speed of the timeline"""
        self.speed = speed

    def add_to_scene(self, ren):
        super(Timeline, self).add_to_scene(ren)
        if self._has_playback_panel:
            ren.add(self.playback_panel)
        [ren.add(timeline) for timeline in self._timelines]
        self._scene = ren