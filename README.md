### *pseyepy:* A python API for acquisition, display, and saving of video from the PS3Eye camera

If you're making use of this package, please let me know! 

I'll be motivated to improve and maintain it if people are benefiting from it.

Reach me at: deverett[at]princeton[dot]edu

----------------------
### About this package

*pseyepy* is a lightweight, cross-platform, and open-source Python interface to the Playstation PS3Eye USB camera.

At this point, the dependencies for the project are:
  * python 3x
  * numpy, cython
  * [libusb](http://libusb.info/)
  * (a substantially modified version of the) [PS3EYEDriver project](https://github.com/inspirit/PS3EYEDriver)
  * [ffmpeg](https://www.ffmpeg.org/)

The important features are:
  * stream simultaneously from as many cameras as you have available usb ports
  * frame rates: up to 150 Hz
  * resolutions: 640x480 or 320x240 pixels 
  * control of camera settings include gain, exposure, white balance, orientation, etc.
  * high-resolution software timestamps  
  * simple gui for real-time video display 
  * save movies to disk

**Contributions** are greatly appreciated! You can make a pull request, or simply email me (address above).

----------------
### Installation

Installation has not yet been thoroughlly tested on all platforms. Eventually I will get around to enabling a pip install. For now:

1. Download libusb and ffmpeg
2. Download the source code, unzip, and navigate to the root directory
3. `python setup.py install`

If this does not work, it's likely a libusb issue. Try adjusting paths such that libusb paths are included by default.

------------
### Examples

Basic usage:
```python
from pseyepy import Camera

# initialize all connected cameras
c = Camera()

# read from the camera/s
frame, timestamp = c.read()
```

Specify specific camera/s:
`c = Camera(0)` # camera at index 0
`c = Camera([0,1])` # cameras at indices 0 and 1

---------------------------------------
### Troubleshooting and known pitfalls

  * The PSEye camera has two LED indicators: a blue light indicating power, and a red light indiciating communication with the computer. If these lights are not on, then their respective functions are not active (although note that you can intentionally destroy these LEDs if you please, and the camera will work fine).
  * If the cameras or API act strangely, try disconnecting and reconnecting the cameras, restarting the Python shell, and running the program again.
  * In general it is recommended to restart the python process before each camera use; it's not technically necessary but it helps avoid some issues.
  * The on-board camera settings can be wonky; changing them in a particular order can have specific effects, that sometimes prove irreversible until you restart the program.
  * The Stream writer currently can drop ~0.01% of frames (likely from the very end of the recording only, details still unclear)

---------
### Todo

  * more documentation
  * build a multithreaded cython option for camera streaming to free the main process
  * importantly: without a threading implementation, Stream to file with cameras of different framerates will result in lowest for all
