import tkinter as tk
import threading
import time
import numpy as np
from PIL import Image, ImageTk

from .cameras import Camera

class Display(tk.Frame):

    def __init__(self, grab_fxn=None, refresh_rate=100, onexit=[]):
     
        if isinstance(grab_fxn, Camera):
            grab_fxn = grab_fxn.read
        
        self.grab_fxn = grab_fxn
        self.refresh_rate = refresh_rate
        self.onexit = onexit
        self._refresh_interval = int(1000/self.refresh_rate)

        # tkinter init
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.end)
        scrn_w = self.root.winfo_screenwidth()
        scrn_h = self.root.winfo_screenheight()
        #self.root.geometry('{}x{}'.format(scrn_w, scrn_h)) # fullscreen

        tk.Frame.__init__(self, self.root)
        self.grid(row=0, column=1)

        self.cvs = None 

        # run main loop
        self.step()
        self.mainloop()

    def grab(self):
        return self.grab_fxn()

    def step(self):
        
        # first iteration:
        if self.cvs is None:
            self.cvs = [] # canvas, canvas_img, photo_img

            imgs,ts = self.grab()
            if imgs is None:
                self.end()
                return

            for i,img in enumerate(imgs):
                canvas = tk.Canvas(self)
                canvas.grid(row=0, column=i)

                photo = ImageTk.PhotoImage(image=Image.fromarray(img))
                cvs_im = canvas.create_image(0, 0, image=photo)

                self.cvs.append([canvas, cvs_im, photo])

        # all iterations
        imgs,ts = self.grab()
        for im,cv in zip(imgs, self.cvs):
            cv[-1] = ImageTk.PhotoImage(image=Image.fromarray(im))
            cv[0].itemconfig(cv[1], image=cv[-1])
        
        self.recall = self.after(self._refresh_interval, self.step)

    def end(self, *args):
        self.after_cancel(self.recall)
        [oe() for oe in self.onexit]
        self.root.destroy()

