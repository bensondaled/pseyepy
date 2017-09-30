from pseyepy import Camera, Display, Stream, cam_count

# -- to begin, the simplest example:

c = Camera() # initialize all connected cameras
frame, timestamp = c.read() # read from the camera


# -- parameters

c = Camera(0) # initialize a specific camera with ID 0
c = Camera([0,1], fps=60, resolution=Camera.RES_LARGE, colour=False) # initialize 2 cameras with ids 0 and 1; parameters by default apply to all cameras requested
c = Camera([0,1], fps=[30, 60], resolution=[Camera.RES_LARGE, Camera.RES_SMALL], colour=[True, False]) # each parameter can be set independently as well
c = Camera([0,1], fps=10, colour=True, gain=50, vflip=[True,False]) # you may also set any of the on-board image parameters upon initialization
c.gain = 20 # parameters can also be set after initializing (but not fps, resolution, or colour)
c.gain[1] = 25 # parameters can be set independently for the cameras


# -- frame-reading

c = Camera([0,1], fps=60, resolution=Camera.RES_LARGE, colour=False)
frames, timestamps = c.read() # read from all cameras
frame0, timestamp0 = c.read(0) # read from a specific camera (camera 0)
frame1, timestamp1 = c.read(1) # read from a specific camera (camera 1)
frames = c.read(timestamp=False) # read frames without retrieving timestamps


# -- live display
c = Camera()
d = Display(c)


# -- save to file
c = Camera()
s = Stream(c, file_name='example_movie.avi')
s.end() # stop acquiring
# for a pseudo-decent live monitor (not nearly as fast as Display):
s = Stream(c, file_name='example_movie.avi', display=True)
s.end() # stop acquiring

##
