import threading
import queue
import multiprocessing as mp
import subprocess as sp
import numpy as np
import time
import os
import queue
import h5py
try:
    import cv2
except ImportError:
    cv2 = None
from .asynchronous import CamDump
from .ui import Display

class OpencvWriter():
    """Pipes to a video file using opencv
    """
    def __init__(self, file_name, shape=(320,240), colour=False, fps=30, timestamps=False, codec='mp4v'):
        """
        shape : w,h
        """
        if cv2 is None:
            raise Exception('Cannot use OpencvWriter without cv2. Try using FFMpegWriter instead, by supplying `klass` to Writer class, or `writer_class` to Stream.')

        self.timestamps = timestamps
        self.colour = colour
        
        fnroot,fnext = os.path.splitext(file_name)
        if fnext == '':
            fnext = '.avi'
        if fnext != '.avi':
            warnings.warn('Destination files for movies should be .avi')
        file_name = '{}{}'.format(fnroot,fnext)
        if self.timestamps:
            self.ts_file_name = '{}_time.txt'.format(fnroot)
            self.ts_file = open(self.ts_file_name, 'a')

        codec = cv2.VideoWriter_fourcc(*codec)
        self.vw = cv2.VideoWriter(file_name, codec, fps, shape, isColor=True)

    def write(self, frame, timestamp=None):
        if self.colour==False:
            writeable = cv2.cvtColor((frame).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        else:
            writeable = frame.astype(np.uint8)
        self.vw.write(writeable)

        if self.timestamps:
            if isinstance(timestamp, (tuple,list,np.ndarray)):
                timestamp = ','.join(['{:0.6f}']*len(timestamp)).format(*timestamp)
            else:
                timestamp = '{:0.6f}'.format(timestamp)
            self.ts_file.write('{}\n'.format(timestamp))

    def end(self):
        if self.timestamps:
            self.ts_file.close()
        self.vw.release()

class FFMpegWriter():
    """Pipes to a video file using ffmpeg on command
    """
    def __init__(self, file_name, shape=(320,240), colour=False, fps=30, timestamps=False, codec='png'):
        """
        shape : w,h
        """
        self.timestamps = timestamps

        fnroot,fnext = os.path.splitext(file_name)
        if fnext == '':
            fnext = '.avi'
        if fnext != '.avi':
            warnings.warn('Destination files for movies should be .avi')
        file_name = '{}{}'.format(fnroot,fnext)
        if self.timestamps:
            self.ts_file_name = '{}_time.txt'.format(fnroot)
            self.ts_file = open(self.ts_file_name, 'a')

        _col = 'rgb24' if colour else 'gray'
        _shape = '{}x{}'.format(*shape)
        _fps = str(int(fps))

        self.cmd =     ['/usr/local/bin/ffmpeg',
            #'-y', # overwrite
            '-f', 'rawvideo',
            '-vcodec','rawvideo',
            '-s', _shape,
            '-pix_fmt', _col,
            '-r', _fps,
            '-i', '-', # pipe
            '-an', # no audio
            '-vcodec', codec,
            file_name ]
        self.proc = sp.Popen(self.cmd, stdin=sp.PIPE, stderr=sp.PIPE)

    def write(self, frame, timestamp=None):
        self.proc.stdin.write(frame.tobytes())
        if self.timestamps:
            if isinstance(timestamp, (tuple,list,np.ndarray)):
                timestamp = ','.join(['{:0.6f}']*len(timestamp)).format(*timestamp)
            else:
                timestamp = '{:0.6f}'.format(timestamp)
            self.ts_file.write('{}\n'.format(timestamp))
	
    def end(self):
        if self.timestamps:
            self.ts_file.close()
        self.proc.stdin.close()
        self.proc.stderr.close()
        self.proc.wait()


def generate_movie_params(cam, file_name, **kw):
    """Given a camera object and a root file_name, format and return file-saving parameters
    """
    if isinstance(file_name, str):
        file_name = [file_name] * len(cam.ids)
        add_idxs = True
    else:
        add_idxs = False

    assert len(file_name)==len(cam.ids), 'Number of unique file names must match number of unique cameras.'
    for i,fn in enumerate(file_name):
        fnroot,fnext = os.path.splitext(fn)
        if add_idxs:
            fnroot = '{}_{}'.format(fnroot, i)
        file_name[i] = fnroot # leaves out extension so writer can handle it

    movie_params = [ dict(   
            file_name = file_name[i],
            shape = cam.resolution[i],
            fps = cam.fps[i],
            colour = cam.colour[i],
            ) for i in range(len(cam.ids)) ]

    for mpr in movie_params:
        mpr.update(kw)

    return movie_params

class Stream():
    """Convenience class to handle the creation of a CamDump and Writer, to grab and save input from a camera
    """
    def __init__(self, cam, file_name=None, display=False, writer_class=None, **kwargs):
        self.cam = cam
        self.file_name = file_name
        self.ques = {}

        if writer_class is None:
            writer_class = Writer.DEFAULT_WRITER_CLASS

        if self.file_name is not None:
            movie_params = generate_movie_params(self.cam, self.file_name, **kwargs)
            self.ques['file'] = queue.Queue()
        if display:
            self.ques['display'] = queue.Queue()

        self.cd = CamDump(self.cam, ques=list(self.ques.values()))

        if self.file_name is not None:
            self.w = Writer(klass=writer_class, que=self.ques['file'], movie_params=movie_params)
        if display:
            d = Display(lambda: self.ques['display'].get(block=False))

    def end(self):
        self.cd.end()
        if self.file_name is not None:
            self.w.end()

class Writer(threading.Thread):
    """Continually reads from a queue and writes to a file
    """
    DEFAULT_WRITER_CLASS = FFMpegWriter # or OpencvWriter
    def __init__(self, klass, que, movie_params={}):
        super().__init__()
   
        self.klass = klass
        self.que = que
        self.movie_params = movie_params
        if isinstance(self.movie_params, dict):
            self.movie_params = [self.movie_params]
        self.kill = threading.Event()
        self.done = threading.Event()

        self.start()

    def run(self):
       
        ffmpws = []
        for mpm in self.movie_params:
            ff = self.klass(timestamps=True, **mpm)
            ffmpws.append(ff)

        while not self.kill.is_set():
            time.sleep(0.005) # wait 5ms, necessary for smooth operation, shouldn't affect framerates b/c this is a thread
            try:
                data,ts = self.que.get(block=False)

                assert len(data) == len(ffmpws), 'Param and cam count mismatch'
                for dat,t,ff in zip(data, ts, ffmpws):
                    ff.write(dat, timestamp=t)

            except queue.Empty:
                pass

        ff.end()
        self.done.set()

    def end(self):
        self.kill.set()
        while not self.done.is_set():
            pass
