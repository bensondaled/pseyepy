import threading
import multiprocessing as mp
import subprocess as sp
import numpy as np
import time
import os
import queue
import h5py

from .asynchronous import CamDump

class Stream():
    """Convenience class to handle the creation of a CamDump and Writer, to grab and save input from a camera
    """
    def __init__(self, cam, file_name):
        self.cam = cam

        if isinstance(file_name, str):
            file_name = [file_name] * len(self.cam.ids)
            add_idxs = True
        else:
            add_idxs = False

        assert len(file_name)==len(self.cam.ids), 'Number of unique file names must match number of unique cameras.'
        for i,fn in enumerate(file_name):
            fnroot,fnext = os.path.splitext(fn)
            if add_idxs:
                fnroot = '{}_{}'.format(fnroot, i)
            file_name[i] = fnroot # leaves out extension so writer can handle it

        movie_params = [ dict(   
                file_name = file_name[i],
                shape = self.cam.resolution[i],
                fps = self.cam.fps[i],
                color = self.cam.color[i],
                ) for i in range(len(self.cam.ids)) ]

        self.que = mp.Queue()

        self.cd = CamDump(self.cam, que=self.que)
        self.w = Writer(que=self.que, movie_params=movie_params)

    def end(self):
        self.w.end()
        self.cd.end()

class FFMpegWriter():
    """Pipes to a video file using ffmpeg on command
    """
    def __init__(self, file_name, shape=(320,240), color=False, fps=30, timestamps=False):
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

        _col = 'rgb24' if color else 'gray'
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
            '-vcodec', 'png',
            file_name ]
        self.proc = sp.Popen(self.cmd, stdin=sp.PIPE, stderr=sp.PIPE)

    def write(self, frame, timestamp=None):
        self.proc.stdin.write(frame.tobytes())
        if self.timestamps:
            if isinstance(timestamp, (tuple,list,np.ndarray)):
                timestamp = ','.join(['{:0.15f}']*len(timestamp)).format(*timestamp)
            else:
                timestamp = '{:0.15f}'.format(timestamp)
            self.ts_file.write('{}\n'.format(timestamp))
	
    def end(self):
        if self.timestamps:
            self.ts_file.close()
        self.proc.stdin.close()
        self.proc.stderr.close()
        self.proc.wait()

class Writer(mp.Process):
    """Continually reads from a queue and writes to a file
    """
    def __init__(self, que, movie_params={}):
        super().__init__()
    
        self.que = que
        self.movie_params = movie_params
        if isinstance(self.movie_params, dict):
            self.movie_params = [self.movie_params]
        self.kill = mp.Event()
        self.done = mp.Event()

        self.start()

    def run(self):
       
        ffmpws = []
        for mpm in self.movie_params:
            ff = FFMpegWriter(timestamps=True, **mpm)
            ffmpws.append(ff)

        while not self.kill.is_set():
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
