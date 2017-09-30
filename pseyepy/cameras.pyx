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

    ctypedef unsigned long long uint64_t

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

    uint64_t ps3eye_grab_frame(int id, unsigned char *frame)
    int ps3eye_get_parameter(int id, ps3eye_parameter param)
    int ps3eye_set_parameter(int id, ps3eye_parameter param, int value)

def cam_count():
    """Count number of available cameras
    """
    ps3eye_init()
    n = ps3eye_count_connected()
    ps3eye_uninit()
    return n

class CtrlList(list):
    """A subclass of list used to control the parameters on board the cameras

    One CtrlList is made per parameter, where each element refers to the current value of this parameter for camera `i`.

    This class is used internally in the Camera class and has no user-intended uses.
    """
    def __init__(self, *args, param_id=None, ids=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.param_id = param_id
        self.ids = ids
        self.nm,self.valid = Camera._PARAMS[self.param_id]
    def __setitem__(self, pos, val):

        # invalid parameter supplied
        if val not in self.valid and int(val) not in self.valid:
            warnings.warn('\nParameter adjustment for {name} aborted.\nAllowed values for {name}: {valid}\nRequested value: {req}'.format(name=self.nm, valid=self.valid, req=val))
            return

        # allow the use of integers, lists, and slices for setting elements of the CtrlList
        if isinstance(pos, int):
            pos = [pos]
        elif isinstance(pos, (list, np.ndarray, tuple)):
            assert all([isinstance(i,int) for i in pos]), 'All requested indices must be integers.'
        elif isinstance(pos, slice):
            start = pos.start or 0
            stop = pos.stop or len(self)
            step = pos.step or 1
            pos = range(start, stop, step)
        _pos = pos

        for pos in _pos:
            # set the parameters on the camera
            ps3eye_set_parameter(self.ids[pos], self.param_id, val)

            # confirm that the parameters changed by reading them back out
            conf = ps3eye_get_parameter(self.ids[pos], self.param_id)
            if conf != val:
                warnings.warn('\nParameter adjustment for "{name}" failed.\nMaybe you supplied an invalid value?\nAllowed values for "{name}": {valid}\nRequested value: {req}\nCurrent value: {cur}'.format(name=self.nm, valid=self.valid, req=val, cur=conf))
                return
            
            # set the list items so they can be viewed, queried
            super().__setitem__(pos, val)

def _getattr_wrapper(name):
    def result(obj):
        return getattr(obj, name)
    return result

def _noset(name):
    def result(obj, val):
        raise Exception('Attribute "{}" cannot be changed after Camera is initialized. Action aborted.'.format(name))
    return result

def _setattr_wrapper(name):
    def result(obj, val):
        cl = getattr(obj, name)
        
        if isinstance(val, (bool, long, float, int)):
            # attributes are always CtrlLists, so an attempt to set them with a scalar means that all elements of the list should be set to this one value
            cl[:] = val
        elif isinstance(val, (list, np.ndarray, tuple)):
            # an iterable can be used to set the attributes if and only if it matches the number of cameras exactly
            if len(val) != len(cl):
                raise Exception('Length of "{}" input ({}) does not match necessary length ({}). Action aborted.'.format(name, len(val), len(cl)))
            for i,v in enumerate(val):
                cl[i] = v
        elif val in [None]:
            warnings.warn('Attribute "{}" cannot be set to None. Action aborted.'.format(name[1:]))
        else:
            warnings.warn('Requested value for attribute "{}" not understood. Action aborted.'.format(name[1:]))
    return result

class Camera():
    """Controller for an arbitrary number of PSEye cameras
    """

    # class constants
    FRAME_DTYPE = np.uint8

    _PARAMS = { 
                PS3EYE_AUTO_GAIN:           ('auto_gain',      [True, False]),
                PS3EYE_AUTO_EXPOSURE:       ('auto_exposure',  [True, False]),
                PS3EYE_AUTO_WHITEBALANCE:   ('auto_whitebalance',[True, False]),
                PS3EYE_GAIN:                ('gain',           list(range(64))),
                PS3EYE_EXPOSURE:            ('exposure',       list(range(256))),
                PS3EYE_REDBALANCE:          ('red_balance',    list(range(256))),
                PS3EYE_BLUEBALANCE:         ('blue_balance',   list(range(256))),
                PS3EYE_GREENBALANCE:        ('green_balance',  list(range(256))),
                PS3EYE_HFLIP:               ('hflip',          [True, False]),
                PS3EYE_VFLIP:               ('vflip',          [True, False]),
                # these are technically implemented but I have found they do not work, or they interefere with other params:
                #PS3EYE_SHARPNESS:           ('sharpness',      list(range(64))),
                #PS3EYE_CONTRAST:            ('contrast',       list(range(256))),
                #PS3EYE_BRIGHTNESS:          ('brightness',     list(range(256))),
                #PS3EYE_HUE:                 ('hue',            list(range(256))),
            }

    RES_SMALL = 0
    RES_LARGE = 1
    _RESOLUTION = { RES_SMALL:(320,240),
                    RES_LARGE:(640,480) }

    def __init__(self, ids=None, resolution=RES_SMALL, fps=60, colour=True, **kwargs):
        """Initialize a new Camera object to control one or many PSEye cameras

        Parameters
        ----------
        ids : int-like / list-like
            ID number/s of cameras to be initialized. All cameras must be handled by a single Camera object
            Example: [0,1]
            Defaults to all connected cameras
        resolution : Camera.RES_SMALL / Camera.RES_LARGE
            RES_SMALL corresponds to (320x240) pixels, and RES_LARGE corresponds to (640x480) pixels
            default: Camera.RES_SMALL
        fps : int
            desired frame rate in frames per second
            The frame rate on the PSEye is quantized to specific levels, and higher frame rates can be achieved with the smaller resolution setting
            Frame rates for RES_SMALL: 30, 40, 50, 60, 75, 100, 125 (although other rates may work)
            Frame rates for RES_LARGE: 15, 30, 40, 50, 60 (although other rates may work)
            Use the Camera.check_fps method to evaluate the empirical frame rate after initializing the object
        colour : True / False
            colour mode returns 3D frames with color in the last (3rd) dimension as RGB
            greyscale (colour=False) returns 2D frames
        kwargs : any of the camera settings detailed below

        Available camera settings include:
            auto_gain (True / False)
            auto_exposure (True / False) - NOT YET IMPLEMENTED
            auto_whitebalance (True / False)
            gain (0-63)
            exposure (0-255)
            red_balance (0-255)
            blue_balance (0-255)
            green_balance (0-255)
            hflip (True / False) - flip frames horizontally upon reading
            vflip (True / False) - flip frames vertically upon reading
        Note that some of these settings interact with each other in strange ways, and you may find it difficult to return to a particular parameter set without restarting the program.
        """

        if isinstance(ids, (int, float, long)):
            ids = [ids]
        elif isinstance(ids, (tuple, np.ndarray)):
            ids = list(ids)
        elif ids is None:
            ids = list(range(cam_count()))
        self._ids = ids

        if isinstance(resolution, (int, float, long)):
            resolution = [self._RESOLUTION[resolution]] * len(ids)
        elif isinstance(resolution, (tuple, list, np.ndarray)):
            assert len(resolution) == len(ids)
            assert all([isinstance(r, (int, float, long)) for r in resolution])
            resolution = [self._RESOLUTION[r] for r in resolution]
        self._resolution = resolution
        self._w, self._h = zip(*resolution)

        if isinstance(fps, (int, float, long)):
            fps = [fps] * len(ids)
        elif isinstance(fps, (tuple, list, np.ndarray)):
            assert len(fps) == len(ids)
            assert all([isinstance(f, (int, float, long)) for f in fps])
        self._fps = fps

        if isinstance(colour, bool):
            colour = [colour] * len(ids)
        elif isinstance(colour, (tuple, list, np.ndarray)):
            assert len(colour) == len(ids)
            assert all([isinstance(c, bool) for c in colour])
        else:
            raise Exception('Color mode not understood, should be True or False.')
        self._colour = colour
        self._format = [PS3EYE_FORMAT_RGB if c else PS3EYE_FORMAT_GRAY for c in colour]
        self._depth = [3 if c else 1 for c in colour] # 2nd 3 will be 1 when grey is implemented

        self._shape = [(y,x,d) if d>1 else (y,x) for y,x,d in zip(self._h, self._w, self._depth)]

        # init context
        ps3eye_init()

        # init all cameras
        count = ps3eye_count_connected()
        self.buffers = {}
        for idx,_id in enumerate(ids):
            if _id >= count:
                ps3eye_uninit()
                raise Exception('No camera available at index {}.\nAvailable cameras: {}'.format(_id, count))
            else:
                success = ps3eye_open(_id, self._w[idx], self._h[idx], fps[idx], self._format[idx])
                if not success:
                    raise Exception('Camera at index {} failed to initialize.'.format(_id))
                self.buffers[_id] = np.bytes_(self._w[idx]*self._h[idx]*self._depth[idx])
        self._timestamps = {}

        # params
        for pconst,(pname,valid) in self._PARAMS.items():
            setattr(Camera, pname, property(fget=_getattr_wrapper('_'+pname), fset=_setattr_wrapper('_'+pname)))
            setattr(self, '_'+pname, CtrlList([ps3eye_get_parameter(i, pconst) for i in ids], param_id=pconst, ids=ids))

        # protected attributes
        protected = ['ids','resolution','w','h','fps','colour','format','depth','shape']
        for p in protected:
            setattr(Camera, p, property(fget=_getattr_wrapper('_'+p), fset=_noset(p)))

        self._ended = False

        atexit.register(self.end)

        # any optional init params supplied
        # performed last because it has the potential to throw and exception, but that should not invalidate the existence of this object
        for k,v in kwargs.items():
            if k in dir(self):
                setattr(self, k, v)
            else:
                warnings.warn('Parameter {} not recognized; ignored.'.format(k))

    def read(self, idx=None, timestamp=True, squeeze=True):
        """Read camera frame/s

        Parameters
        ----------
        idx : int / list-like / None
            index/indices of camera/s from which to read
            if None, reads from all cameras controlled by this object
        timestamp : True / False
            return timestamp along with frame
            if True, returns (frames, timestamps)
        squeeze : True / False
            if False, returns a list of frames/timestamps even when only one camera is controlled

        Returns
        -------
        list of frames, one per camera controlled by the object
        """
        was_scalar = False
        if idx is None:
            idx = list(range(len(self.ids)))
        elif isinstance(idx, (list,np.ndarray)):
            assert all([i<len(self.ids) for i in idx])
        elif isinstance(idx, (float,int,long)):
            idx = [idx]
            was_scalar = True

        imgs,ts = [None for i in idx],[None for i in idx]
        
        for j,i in enumerate(idx):
            _id = self.ids[i]
            tstmp = ps3eye_grab_frame(_id, self.buffers[_id])
            img = np.frombuffer(self.buffers[_id], dtype=self.FRAME_DTYPE)
            imgs[j] = img.reshape(self.shape[i])
            ts[j] = tstmp*1e-6

        if was_scalar:
            imgs = imgs[0]
            ts = ts[0]

        if squeeze and len(imgs)==1:
            imgs = imgs[0]
            ts = ts[0]

        if timestamp:
            return (imgs, ts)
        else:
            return imgs

    def check_fps(self, n_seconds=10):
        """Empirical measurement of frame rate in frames per second

        Parameters
        ----------
        n_seconds : int
            number of seconds over which to acquire frames for frame rate analysis (you will need to wait this duration for each camera controlled)

        Returns
        -------
        timestamps from each camera

        Running this method will print out an analysis of the frame rate
        """

        tss = []
        for i in range(len(self.ids)):
            n_frames = self.fps[i] * n_seconds
            ts = []
            for f in range(n_frames):
                _,tsi = self.read(i)
                ts.append(tsi)
            ts = np.array(ts)
            tss.append(ts)
            dif = np.diff(ts)

            desired_interval = 1/self.fps[i]
            mean_interval = np.mean(dif)
            mean_rate = 1/mean_interval
            std_interval = np.std(dif)
            within_1ms = np.mean(np.abs(desired_interval - dif)<=0.001)
            within_2ms = np.mean(np.abs(desired_interval - dif)<=0.002)
            above_1ms = np.mean((dif - desired_interval)>0.001)
            below_1ms = np.mean((dif - desired_interval)<-0.001)
            above_2ms = np.mean((dif - desired_interval)>0.002)
            below_2ms = np.mean((dif - desired_interval)<-0.002)

            print("""Camera {}:\t
                    Mean rate: {:0.3f} fps (desired={:0.0f})\t
                    Mean interval: {:0.3f} ms (desired={:0.3f})\t
                    Std interval: {:0.3f} ms ({:0.1f}%)\t
                    Within 1 ms of desired (={} fps): {:0.2f}%\t
                    Within 2 ms of desired (={} fps): {:0.2f}%\t
                    >1 ms longer than desired: {:0.2f}%\t
                    >1 ms shorter than desired: {:0.2f}%\t
                    >2 ms longer than desired: {:0.2f}%\t
                    >2 ms shorter than desired: {:0.2f}%
                    """.format(i, mean_rate, self.fps[i], 1e3*mean_interval, 1e3/self.fps[i], 1e3*std_interval, 100*std_interval/mean_interval, self.fps[i], 100*within_1ms, self.fps[i], 100*within_2ms, 100*above_1ms, 100*below_1ms, 100*above_2ms, 100*below_2ms))

        return tss

    def end(self):
        """Close the object; this should be run before creating a new Camera object, and before quitting Python (for latter, it does so automatically if not called explicitly)
        """
        if not self._ended:
            for _id in self.ids:
                ps3eye_close(_id)
            ps3eye_uninit()
            self._ended = True

