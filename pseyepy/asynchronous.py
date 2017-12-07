import threading
import queue
import time

class CamDump(threading.Thread):
    """Continually reads from a camera and dumps into queue/s
    Is implemented as thread currently b/c camera class only runs in main process and cannot be forked
    This is a hard problem
    """
    def __init__(self, cam, ques):
        super().__init__()

        self.cam = cam
        self.ques = ques

        if isinstance(self.ques, queue.Queue):
            self.ques = [self.ques]

        self.kill = threading.Event()
        self.done = threading.Event()
        
        self.start()

    def run(self):

        while not self.kill.is_set():
            time.sleep(0.005) # wait 5ms, necessary for smooth operation, shouldn't affect framerates b/c this is a thread
            frame,ts = self.cam.read(timestamp=True, squeeze=False)

            for que in self.ques:
                que.put((frame,ts))

        self.done.set()

    def end(self):

        self.kill.set()
        while not self.done.is_set():
            pass
