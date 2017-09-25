import threading
import multiprocessing as mp
import numpy as np
import time
import queue
import h5py

from .cameras import Camera
from .ui import Display

class IO(threading.Thread):
    """Continually reads from a camera and dumps into queue/s
    """
    def __init__(self, cam, file_name=None, writer_kw={}):
        super(IO, self).__init__()

        self.cam = cam
        self.file_name = file_name

        # if saving
        if self.file_name is not None:
            self.save_que = mp.Queue()
            self.writer = Writer(que=self.save_que, file_name=file_name, shape=self.cam.shape, **writer_kw)

        self.kill = mp.Event()
        self.complete = mp.Event()
        
        self.start()

    def run(self):
        debug = 0
        while not self.kill.is_set():
            frame = self.cam.read()

            if self.file_name is not None:
                self.save_que.put(frame)
                debug += 1
                print('Writer:', debug)

        self.complete.set()

    def end(self):

        self.kill.set()
        while not self.complete.is_set():
            pass

        if self.file_name is not None:
            self.writer.kill.set()
            while not self.writer.complete.is_set():
                pass

class Writer(mp.Process):
    """Continually saves to file the contents read out from a queue
    """
    def __init__(self, que, file_name, shape, buffer_size=2000, dataset_resize=30000):

        super(mp.Process, self).__init__()

        # Saving params
        if not file_name.endswith('.h5'):
            file_name += '.h5'
        self.file_name = file_name
        self.buffer_size = buffer_size
        self.dataset_resize = dataset_resize

        self.shape = shape

        # Flags and containers
        self.que = que
        self.kill = mp.Event()
        self.complete = mp.Event()

        self.start()
        
    def run(self):
        
        # Setup hdf5 file and datasets
        self.vw_f = h5py.File(self.file_name,'w')
        self.vw,self.vwts = [],[]
        for i,(y,x,d) in enumerate(self.shape):
            vw = self.vw_f.create_dataset('mov{}'.format(i), (self.dataset_resize, y, x, d), maxshape=(None, y, x, d), dtype='uint8', compression=None) 
            vwts = self.vw_f.create_dataset('ts{}'.format(i), (self.dataset_resize,2), maxshape=(None,2), dtype=np.float64, compression=None)
            self.vw.append(vw)
            self.vwts.append(vwts)
           
        # Counters and buffers
        _sav_idx = [0]*len(self.shape) # index within hdf5 dataset
        _buf_idx = [0]*len(self.shape) # index of buffer
        _saving_buf,_saving_ts_buf = [],[]
        for i in range(len(self.shape)):
            y,x,d = self.shape[i]
            sb = np.empty((self.buffer_size,y,x,d), dtype=Camera.FRAME_DTYPE)
            stb = np.empty((self.buffer_size,2), dtype=np.float64)
            _saving_buf.append(sb)
            _saving_ts_buf.append(stb)

        # Main loop
        debug = 0
        while not self.kill.is_set():

            try:
                frames = self.que.get(block=False)
                debug += 1
                print('Saver:', debug, '\n')
                ts = 42.
            except queue.Empty:
                continue

            for di,frame in enumerate(frames):
                if self.vw[di].shape[0]-_sav_idx[di] <= self.buffer_size:
                    assert self.vw[di].shape[0] == self.vwts[di].shape[0], 'Frame and timestamp dataset lengths are mismatched.'
                    new_vw_size = tuple([self.vw[di].shape[0]+self.dataset_resize] + list(self.vw[di].shape[1:]))
                    new_vwts_size = tuple([self.vwts[di].shape[0]+self.dataset_resize] + list(self.vwts[di].shape[1:]))
                    self.vw[di].resize(new_vw_size)
                    self.vwts[di].resize(new_vwts_size)
                
                # add new data to in-memory buffer
                _saving_buf[di][_buf_idx[di]] = frame
                _saving_ts_buf[di][_buf_idx[di]] = ts
                _buf_idx[di] += 1

                # if necessary, flush out buffer to hdf dataset
                if _buf_idx[di] >= self.buffer_size:
                    self.vw[di][_sav_idx[di]:_sav_idx[di]+_buf_idx[di],:,:] = _saving_buf[di][:_buf_idx[di]]
                    self.vwts[di][_sav_idx[di]:_sav_idx[di]+_buf_idx[di],:] = _saving_ts_buf[di][:_buf_idx[di]]
                    _sav_idx[di] += _buf_idx[di]
                    _buf_idx[di] = 0

        # final flush:
        for di in range(len(self.shape)):
            self.vw[di][_sav_idx[di]:_sav_idx[di]+_buf_idx[di],:,:] = _saving_buf[di][:_buf_idx[di]]
            self.vwts[di][_sav_idx[di]:_sav_idx[di]+_buf_idx[di]] = _saving_ts_buf[di][:_buf_idx[di]]
            _sav_idx[di] += _buf_idx[di]
            # cut off all unused allocated space 
            new_vw_size = tuple([_sav_idx[di]] + list(self.vw[di].shape[1:]))
            new_vwts_size = tuple([_sav_idx[di]] + list(self.vwts[di].shape[1:]))
            self.vw[di].resize(new_vw_size)
            self.vwts[di].resize(new_vwts_size)

        self.vw_f.close()
        self.complete.set()

class Playback():
    """TODO: chunk the reading so it's not painfully slow
    """
    def __init__(self, file_name):
        self.handle = h5py.File(file_name, 'r')
        self.mov_datasets = [i for i in self.handle if 'mov' in i]
        self.i = [0 for md in self.mov_datasets]
        
        self.disp = Display(self.next, onexit=[self.end])

    def next(self):
        return [self.handle[md][i] for md,i in zip(self.mov_datasets, self.i)]

    def end(self):
        self.handle.close()
