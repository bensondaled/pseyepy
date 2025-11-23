from pseyepy import Camera
from pseyepy.ui import Display

c = Camera([0], fps=120, resolution=Camera.RES_SMALL, colour=False)
d = Display(c)  # begin the display