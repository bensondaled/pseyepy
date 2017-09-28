##

from pseyepy import Camera, Display, Stream, cam_count

# init a camera
c = Camera([0,1], fps=60, resolution=Camera.RES_LARGE, color=False)

# live display the camera
d = Display(c)

# save to file
s = Stream(c, file_name='example_movie.avi')

##
