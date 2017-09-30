import tkinter as tk
import threading
import time
import numpy as np
from PIL import Image, ImageTk

from .cameras import Camera

class Display(tk.Tk):

    def __init__(self, grab_fxn=None, refresh_rate=45, onexit=[]):
     
        tk.Tk.__init__(self, None)
        scrn_w = self.winfo_screenwidth()
        scrn_h = self.winfo_screenheight()
        self.geometry('{}x{}'.format(scrn_w, scrn_h)) # fullscreen
        self.protocol("WM_DELETE_WINDOW", self.end)
        self.onexit = onexit
        self.grid()
        
        if isinstance(grab_fxn, Camera):
            self.cam = grab_fxn
            grab_fxn = lambda: self.cam.read(timestamp=True, squeeze=False)
        else:
            self.cam = None
        
        self.grab_fxn = grab_fxn
        self.refresh_rate = refresh_rate
        self._refresh_interval = int(1000/self.refresh_rate)

        self.cvs = None 

        # run main loop
        self.title('Camera Display')
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
                
                # canvas for this camera
                canvas = ImgCanvas(self, img)
                canvas.grid(column=i+1, row=0, sticky='EW')
                self.cvs.append(canvas)

                # sliders for this camera
                if self.cam is not None:
                    for pidx,(pname,valid) in enumerate(self.cam._PARAMS.values()):
                        minn = int(min(valid))
                        maxx = int(max(valid))
                        fxn = lambda val, pn=pname, ii=i: self.set_param(ii, pn, val)
                        sc = tk.Scale(self, from_=minn, to=maxx, orient=tk.HORIZONTAL, length=img.shape[1], command=fxn)
                        sc.set(getattr(self.cam, pname)[i])
                        sc.grid(column=i+1, row=1+pidx)
                        if i==0:
                            label = tk.Label(self, text=pname)
                            label.grid(column=0, row=1+pidx)

        # all iterations
        imgs,ts = self.grab()
        for im,cv in zip(imgs, self.cvs):
            cv.set_img(im)
        
        self.recall = self.after(self._refresh_interval, self.step)

    def set_param(self, idx, name, val):
        if self.cam is not None:
            getattr(self.cam, name)[int(idx)] = int(val)

    def end(self, *args):
        self.after_cancel(self.recall)
        [oe() for oe in self.onexit]
        self.destroy()

class ImgCanvas(tk.Canvas):
    def __init__(self, parent, img, **kwargs):
        """
        img : np.ndarray
        """

        kwargs['width'] = kwargs.get('width', img.shape[1])
        kwargs['height'] = kwargs.get('height', img.shape[0])
        kwargs['highlightthickness'] = kwargs.get('highlightthickness', 0)

        tk.Canvas.__init__(self,parent,**kwargs)

        self.cvs_im = None
        self.set_img(img)
        
    def set_img(self, img):
        pimg = Image.fromarray(img)
        #pimg = pimg.resize((320,240), Image.ANTIALIAS)
        self.photo = ImageTk.PhotoImage(image=pimg)
        if self.cvs_im is None:
            center = (img.shape[1]//2, img.shape[0]//2)
            self.cvs_im = self.create_image(center[0], center[1], image=self.photo)
        else:
            self.itemconfig(self.cvs_im, image=self.photo)

