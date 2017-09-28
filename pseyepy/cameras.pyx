# distutils: language=c++

from libcpp cimport bool as cbool
import atexit
import warnings
import time
import numpy as np
import multiprocessing as mp
import threading

# PS3EYE API definitions
cdef extern from "ps3eye_capi.h":

    ctypedef enum ps3eye_format: 
        PS3EYE_FORMAT_BAYER
        PS3EYE_FORMAT_RGB
        PS3EYE_FORMAT_BGR
        PS3EYE_FORMAT_GRAY
    ctypedef enum ps3eye_parameter: 
        PS3EYE_AUTO_GAIN,           # [false, true]
        PS3EYE_GAIN,                # [0, 63]
        PS3EYE_AUTO_WHITEBALANCE,   # [false, true]
        PS3EYE_AUTO_EXPOSURE,       # [false, true]
        PS3EYE_EXPOSURE,            # [0, 255]
        PS3EYE_SHARPNESS,           # [0 63]
        PS3EYE_CONTRAST,            # [0, 255]
        PS3EYE_BRIGHTNESS,          # [0, 255]
        PS3EYE_HUE,                 # [0, 255]
        PS3EYE_REDBALANCE,          # [0, 255]
        PS3EYE_BLUEBALANCE,         # [0, 255]
        PS3EYE_GREENBALANCE,        # [0, 255]
        PS3EYE_HFLIP,               # [false, true]
        PS3EYE_VFLIP                # [false, true]

    void ps3eye_init()
    void ps3eye_uninit()
    int ps3eye_count_connected()
    int ps3eye_get_unique_identifier(   int id,
                                        char *out_identifier,
                                        int max_identifier_length )

    cbool ps3eye_open(   int id, 
                        int width, 
                        int height, 
                        int fps, 
                        ps3eye_format outputFormat )
    void ps3eye_close(int id)

    void ps3eye_grab_frame(int id, unsigned char *frame)
    int ps3eye_get_parameter(int id, ps3eye_parameter param)
    int ps3eye_set_parameter(int id, ps3eye_parameter param, int value)

def cam_count():
    ps3eye_init()
    n = ps3eye_count_connected()
    ps3eye_uninit()
    return n

class CtrlList(list):
    def __init__(self, *args, param_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.param_id = param_id
        self.nm,self.valid = Camera._PARAMS[self.param_id]
    def __setitem__(self, pos, val):
        if val not in self.valid:
            warnings.warn('\nParameter adjustment for {name} aborted.\nAllowed values for {name}: {valid}\nRequested value: {req}'.format(name=self.nm, valid=self.valid, req=val))
            return
        ps3eye_set_parameter(pos, self.param_id, val)
        conf = ps3eye_get_parameter(pos, self.param_id)
        if conf != val:
            warnings.warn('\nParameter adjustment for {name} failed.\nAllowed values for {name}: {valid}\nRequested value: {req}'.format(name=self.nm, valid=self.valid, req=val))
            return
        super().__setitem__(pos, val)

class Camera():
    """
    cam.gain[1] = 42
    """
    FRAME_DTYPE = np.uint8

    _PARAMS = { 
                PS3EYE_AUTO_GAIN:           ('auto_gain',      [True, False]),
                #PS3EYE_AUTO_EXPOSURE:      ('auto_exposure',  [True, False]), # until I debug auto-exposure
                # this may help: https://android.googlesource.com/kernel/exynos.git/+/9bd6eb82b787bce6600659aef25b8c23ec601445/drivers/media/video/gspca/ov534.c
                PS3EYE_AUTO_WHITEBALANCE:   ('auto_whitebalance',[True, False]),
                PS3EYE_GAIN:                ('gain',           list(range(64))),
                PS3EYE_EXPOSURE:            ('exposure',       list(range(256))),
                PS3EYE_SHARPNESS:           ('sharpness',      list(range(64))),
                PS3EYE_CONTRAST:            ('contrast',       list(range(256))),
                PS3EYE_BRIGHTNESS:          ('brightness',     list(range(256))),
                PS3EYE_HUE:                 ('hue',            list(range(256))),
                PS3EYE_REDBALANCE:          ('red_balance',    list(range(256))),
                PS3EYE_BLUEBALANCE:         ('blue_balance',   list(range(256))),
                PS3EYE_GREENBALANCE:        ('green_balance',  list(range(256))),
                PS3EYE_HFLIP:               ('hflip',          [True, False]),
                PS3EYE_VFLIP:               ('vflip',          [True, False]),
            }

    RES_SMALL = 0
    RES_LARGE = 1
    _RESOLUTION = { RES_SMALL:(320,240),
                    RES_LARGE:(640,480) }
    def __init__(self, ids, resolution=RES_SMALL, fps=60, color=True):

        if isinstance(ids, (int, float, long)):
            ids = [ids]
        elif isinstance(ids, (tuple, np.ndarray)):
            ids = list(ids)
        self.ids = ids

        if isinstance(resolution, (int, float, long)):
            resolution = [self._RESOLUTION[resolution]] * len(self.ids)
        elif isinstance(resolution, (tuple, list, np.ndarray)):
            assert len(resolution) == len(self.ids)
            assert all([isinstance(r, (int, float, long)) for r in resolution])
            resolution = [self._RESOLUTION[r] for r in resolution]
        self.resolution = resolution
        self.w, self.h = zip(*self.resolution)

        if isinstance(fps, (int, float, long)):
            fps = [fps] * len(self.ids)
        elif isinstance(fps, (tuple, list, np.ndarray)):
            assert len(fps) == len(self.ids)
            assert all([isinstance(f, (int, float, long)) for f in fps])
        self.fps = fps

        if isinstance(color, bool):
            color = [color] * len(self.ids)
        elif isinstance(color, (tuple, list, np.ndarray)):
            assert len(color) == len(self.ids)
            assert all([isinstance(c, bool) for c in color])
        else:
            raise Exception('Color mode not understood, should be True or False.')
        self.color = color
        self.format = [PS3EYE_FORMAT_RGB if c else PS3EYE_FORMAT_GRAY for c in self.color]
        self.depth = [3 if c else 1 for c in self.color] # 2nd 3 will be 1 when grey is implemented

        self.shape = [(y,x,d) if d>1 else (y,x) for y,x,d in zip(self.h, self.w, self.depth)]

        # init context
        ps3eye_init()

        # init all cameras
        count = ps3eye_count_connected()
        self.buffers = {}
        for idx,_id in enumerate(self.ids):
            if _id >= count:
                ps3eye_uninit()
                raise Exception('No camera available at index {}.\nAvailable cameras: {}'.format(_id, count))
            else:
                success = ps3eye_open(_id, self.w[idx], self.h[idx], self.fps[idx], self.format[idx])
                if not success:
                    raise Exception('Camera at index {} failed to initialize.'.format(_id))
                self.buffers[_id] = np.bytes_(self.w[idx]*self.h[idx]*self.depth[idx])

        # params
        for pconst,(pname,valid) in self._PARAMS.items():
            setattr(self, pname, CtrlList([ps3eye_get_parameter(i, pconst) for i in self.ids], param_id=pconst))

        self._ended = False
        atexit.register(self.end)

    def read(self, timestamp=True):
        """Read a frame from each camera
        """
        imgs,ts = [],[]
        for idx,_id in enumerate(self.ids):
            ps3eye_grab_frame(_id, self.buffers[_id])
            img = np.frombuffer(self.buffers[_id], dtype=self.FRAME_DTYPE)
            ts.append((time.clock(), time.time()))
            imgs.append(img.reshape(self.shape[idx]))
        if timestamp:
            return (imgs, ts)
        else:
            return imgs

    def check_fps(self):
        """Empirical measurement of frame rate in frames per second
        """
        dts = []
        for i in range(100):
            t0 = time.time()
            self.read()
            dts.append(time.time()-t0)
        return 1/np.mean(dts)

    def end(self):
        """Close object
        """
        if not self._ended:
            for _id in self.ids:
                ps3eye_close(_id)
            ps3eye_uninit()
            self._ended = True

