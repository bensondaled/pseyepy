from pseyepy import Camera, Live

# example 1: main process, simple camera view
cam = Camera([0,1], resolution=Camera.RES_LARGE, fps=60)
l = Live(cam=cam)

# example 2: camera as a process

# things to include:
# setting bulk params

## todo:
# allow init to take kwargs for all params
# fix autoexposure
# implement all control of framerate, color, and size
# allow different resolutions, color modes, framerates per cam
