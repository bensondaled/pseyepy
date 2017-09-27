import threading
import multiprocessing as mp
import subprocess as sp
import numpy as np
import time
import os
import queue
import h5py

from .cameras import Camera
from .ui import Display

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
            if fnext == '':
                fnext = '.avi'
            if fnext != '.avi':
                warnings.warn('Destination files for movies should be .avi')
            if add_idxs:
                fnroot = '{}_{}'.format(fnroot, i)
            file_name[i] = '{}{}'.format(fnroot,fnext)

        ffmpeg_params = [ dict(   
                file_name = file_name[i],
                shape = self.cam.resolution[i],
                fps = self.cam.fps[i],
                color = self.cam.color[i],
                ) for i in range(len(self.cam.ids)) ]

        self.que = mp.Queue()

        self.cd = CamDump(self.cam, que=self.que)
        self.w = Writer(que=self.que, ffmpeg_params=ffmpeg_params)

    def end(self):
        self.w.end()
        self.cd.end()

class FFMpegWriter():
    """Pipes to a video file using ffmpeg on command
    """
    def __init__(self, file_name, shape=(320,240), color=False, fps=30):
        """
        shape : w,h
        """

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

    def write(self, frame):
        self.proc.stdin.write(frame.tobytes())
	
    def end(self):
        self.proc.stdin.close()
        self.proc.stderr.close()
        self.proc.wait()

class Writer(mp.Process):
    """Continually reads from a queue and writes to a file
    """
    def __init__(self, que, ffmpeg_params={}):
        super().__init__()
    
        self.que = que
        self.ffmpeg_params = ffmpeg_params
        if isinstance(self.ffmpeg_params, dict):
            self.ffmpeg_params = [self.ffmpeg_params]
        self.kill = mp.Event()
        self.done = mp.Event()

        self.start()

    def run(self):
       
        ffmpws = []
        for ffp in self.ffmpeg_params:
            f = FFMpegWriter(**ffp)
            ffmpws.append(f)

        while not self.kill.is_set():
            try:
                data = self.que.get(block=False)

                assert len(data) == len(ffmpws), 'Param and cam count mismatch'
                for dat,f in zip(data, ffmpws):
                    f.write(dat)

            except queue.Empty:
                pass

        f.end()
        self.done.set()

    def end(self):
        self.kill.set()
        while not self.done.is_set():
            pass

class CamDump(threading.Thread):
    """Continually reads from a camera and dumps into queue/s
    Is implemented as thread currently b/c camera class only runs in main thread
    """
    def __init__(self, cam, que):
        super().__init__()

        self.cam = cam
        self.que = que

        self.kill = mp.Event()
        self.done = mp.Event()
        
        self.start()

    def run(self):
        while not self.kill.is_set():
            frame = self.cam.read()

            self.que.put(frame)

        self.done.set()

    def end(self):

        self.kill.set()
        while not self.done.is_set():
            pass
