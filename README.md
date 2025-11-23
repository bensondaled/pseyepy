### *pseyepy:* a python API for acquisition, display, and saving of video from the PS3Eye camera

----------------------

> **📦 Windows-Ready Fork**  
> This is a fork of [bensondaled/pseyepy](https://github.com/bensondaled/pseyepy) with **full Windows support**. The original project had broken Windows builds due to Python 2 compatibility issues and missing MSVC-built dependencies. This fork provides:
> - ✅ **Python 3.13+ support** with fixed Cython code
> - ✅ **Windows 10/11 native builds** using Visual Studio 2022 (MSVC)
> - ✅ **Pre-built libusb binaries** included for seamless Windows installation
> - ✅ **Modern packaging** with `pyproject.toml` for PEP 517/518 compliance
> - ✅ **Works out-of-the-box**: `pip install .` just works on Windows
>
> See [Changes_windows-install.md](Changes_windows-install.md) for detailed technical changes.

----------------------
### About this package

*pseyepy* is a lightweight, cross-platform, and open-source Python interface to the Playstation PS3Eye USB camera. Its core is a wrapper of a C API that derives from the excellent [PS3EYEDriver project](https://github.com/inspirit/PS3EYEDriver). 


At this point, the dependencies for the project are:
  * python 3x
  * numpy, cython
  * [libusb](http://libusb.info/)
  * [ffmpeg](https://www.ffmpeg.org/)

The important features are:
  * stream simultaneously from as many cameras as you have available usb ports
  * frame rates: up to 150 Hz
  * resolutions: 640x480 or 320x240 pixels 
  * control of camera settings include gain, exposure, white balance, orientation, etc.
  * high-resolution software timestamps  
  * simple gui for real-time video display 
  * save movies to disk
  
**Contributions** are greatly appreciated!

----------------
### Installation

#### Windows (This Fork)

**Prerequisites:**
- Python 3.8 or later
- Visual Studio 2022 Build Tools or Visual Studio 2022 (for compilation)
- Git (to clone the repository)

**Quick Install:**
```bash
# Clone this fork
git clone https://github.com/anmagx/pseyepy.git
cd pseyepy

# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate

# Install
pip install .
```

**What's Included:**
- Pre-built MSVC-compatible `libusb-1.0.dll` (no manual libusb setup needed!)
- All Python 3 compatibility fixes
- Proper MSVC compiler flags and build configuration

**Testing:**
```python
import pseyepy
from pseyepy import cam_count
print(f"Cameras detected: {cam_count()}")
```

#### Linux / macOS (Original Instructions)

Installation has not yet been thoroughly tested on all platforms. Eventually I will get around to enabling a pip install. For now:

0. (If you are on Windows: download & install libusb; Mac and Linux are handled without this step)
1. Download the source code, unzip, and navigate to the root directory
2. `sudo python setup.py install`

If that does not work, it's likely a libusb issue. Try adjusting paths such that libusb paths are included by default.

3. (If you want to use ffmpeg for saving, download and install ffmpeg)

------------
### Examples

Basic usage:
```python
from pseyepy import Camera

# initialize all connected cameras
c = Camera()

# read from the camera/s
frame, timestamp = c.read()

# when finished, close the camera
c.end()
```

You may specify specific camera/s:
```python
c = Camera(0) # camera at index 0
```

```python
c = Camera([0,1]) # cameras at indices 0 and 1
```

Set initialization parameters for your camera/s:
```python
c = Camera([0,1], fps=60, resolution=Camera.RES_LARGE, colour=False)
```
*Note that frame rate, resolution, and colour are the 3 parameters that cannot be changed after initializing.*

Set initialization parameters for each camera independently:
```python
c = Camera([0,1], fps=[30, 60], resolution=[Camera.RES_LARGE, Camera.RES_SMALL], colour=[True, False])
```

Set mutable image acquisition parameters upon initialization:
```python
c = Camera(fps=30, colour=[False,True], gain=50, vflip=[True, False])
```
*The mutable parameters include gain, exposure, whitebalance, vflip, hflip. See docstring for full details.*

Set parameters after initialization:
```python
c.exposure = 23
```

For each camera independently:
```python
c.exposure[0] = 23
c.exposure[1] = 45
```

Read from all cameras:
```python
frames, timestamps = c.read()
```

Read from a specific camera:
```python
frame1, timestamp1 = c.read(1) # read from camera at index 1
```

Live display of camera feed with parameter controls:
```python
from pseyepy import Camera, Display

c = Camera() # initialize a camera
d = Display(c) # begin the display
```

Stream camera data to a file using ffmpeg:
```python
from pseyepy import Camera, Stream

c = Camera() # initialize a camera
s = Stream(c, file_name='example_movie.avi', codec='png') # begin saving data to files

# when finished, close the stream
s.end()
```

Stream to file while also displaying (beta):
```python
s = Stream(c, file_name='example_movie.avi', display=True)

# when finished, close the stream
s.end()
```

---------------------------------------
### Troubleshooting and known pitfalls

  * The PSEye camera has two LED indicators: a blue light indicating power, and a red light indicating communication with the computer. If these lights are not on, then their respective functions are not active (although note that you can intentionally destroy these LEDs if you please, and the camera will work fine).
  * If the cameras or API act strangely, try disconnecting and reconnecting the cameras, restarting the Python shell, and running the program again.
  * In general it is recommended to restart the python process before each camera use; it's not technically necessary but it helps avoid some issues.
  * The on-board camera settings can be wonky; changing them in a particular order can have specific effects, that sometimes prove irreversible until you restart the program.
  * The Stream writer currently can drop ~0.01% of frames (likely from the very end of the recording only, details still unclear)
  * On Ubuntu 18.04 in order to get pseyepy to work in some instances it was necessary to install libusb. This could be done through ```sudo apt-get install libusb-1.0-0-dev``` or, if in a conda environment, with ```conda install -c conda-forge libusb```
  * **Windows-specific**: If you get `ImportError: DLL load failed`, ensure you're using Python 3.8+ and Visual Studio 2022 Build Tools are installed

---------------------------------------
### Third-Party Components

This package includes:
- **libusb-1.0** (LGPL v2.1): Pre-built Windows DLL for USB device access
  - License: GNU Lesser General Public License v2.1
  - Source: https://github.com/libusb/libusb
  - Full license text: See `pseyepy/_libs/COPYING`
  - The LGPL allows this library to be used with Apache-licensed code via dynamic linking

For full third-party notices, see [THIRD_PARTY_NOTICES.txt](pseyepy/THIRD_PARTY_NOTICES.txt)

---------
### Todo

  * more documentation
  * build a multithreaded cython option for camera streaming to free the main process
  * importantly: without a threading implementation, Stream to file with cameras of different framerates will result in lowest for all

---------
### Contributing

Contributions are greatly appreciated! This fork focuses on Windows compatibility and modern Python support. If you encounter issues or have improvements, please open an issue or pull request.

**Upstream**: This is a fork of [bensondaled/pseyepy](https://github.com/bensondaled/pseyepy). Consider contributing improvements back to the original project where applicable.

### License

This project is licensed under the **Apache License 2.0** - see [LICENSE](LICENSE) for details.

**Third-party dependencies**:
- libusb-1.0 is licensed under **LGPL v2.1** and is dynamically linked (see `pseyepy/_libs/COPYING`)
- PS3EYEDriver components maintain their original licenses
