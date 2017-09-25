##

from pseyepy import Camera, Display, IO, Playback

# init a camera
c = Camera([0], fps=5, resolution=Camera.RES_SMALL)

# live display the camera
d = Display(c)

# save to file
io = IO(c, file_name='out.h5')

# play back a saved file
p = Playback('out.h5')



##
