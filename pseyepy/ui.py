import tkinter as tk
import threading
import time
import numpy as np
from PIL import Image, ImageTk

class Live(tk.Frame):

    def __init__(self, cam):
       
        # camera
        self.cam = cam
        ncams = len(self.cam.ids)
        empty = np.zeros(self.cam.resolution)
        
        # tkinter init
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.end)
        scrn_w = self.root.winfo_screenwidth()
        scrn_h = self.root.winfo_screenheight()
        #self.root.geometry('{}x{}'.format(scrn_w, scrn_h)) # fullscreen

        tk.Frame.__init__(self, self.root)
        self.grid(row=0, column=1)

        # image frames
        self.cvs = [] # canvas, canvas_img, photo_img
        for i in range(ncams):
            canvas = tk.Canvas(self)
            canvas.grid(row=0, column=i)

            photo = ImageTk.PhotoImage(image=Image.fromarray(empty))
            cvs_im = canvas.create_image(0, 0, image=photo)

            self.cvs.append([canvas, cvs_im, photo])

        # run main loop
        self.step()
        self.mainloop()

    def step(self):
        imgs = self.cam.read()
        for im,cv in zip(imgs, self.cvs):
            cv[-1] = ImageTk.PhotoImage(image=Image.fromarray(im))
            cv[0].itemconfig(cv[1], image=cv[-1])
        
        self.recall = self.after(int(1000/self.cam.fps), self.step)

    def end(self, *args):
        self.after_cancel(self.recall)
        self.root.destroy()

