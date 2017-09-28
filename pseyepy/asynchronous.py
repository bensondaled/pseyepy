import threading
import multiprocessing as mp

class CamDump(threading.Thread):
    """Continually reads from a camera and dumps into queue/s
    Is implemented as thread currently b/c camera class only runs in main process and cannot be forked
    This is a hard problem
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
            frame,ts = self.cam.read(timestamp=True)

            self.que.put((frame,ts))

        self.done.set()

    def end(self):

        self.kill.set()
        while not self.done.is_set():
            pass
