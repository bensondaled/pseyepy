A python API for acquisition and saving of video from the PS3Eye camera.
If you're making use of this package, please let me know! I'll be motivated to improve and maintain it if people are benefiting from it.
Reach me at: deverett[at]princeton[dot]edu

Features:
    * stream simultaneously from as many cameras as you have available usb ports
    * frame rates from arbitrarily low to 125+ fps
    * resolutions 640x480 or 320x240
    * control of camera settings include gain, exposure, white balance, hue, brightness, contrast, flips, etc.
    * high-resolution timestamps
    * simple gui for real-time video display
    * save movies to file/s

This package is based on open-source libraries compatible with macOS, Windows, and Linux:
    * libusb
    * [a substantially modified version of the] PS3EYEDriver project (https://github.com/inspirit/PS3EYEDriver)
    * ffmpeg (only needed for saving movies)

TODO:
    * for stream saving: implement strict match between frame count and timestamp count
    * generalize paths for installation (libusb, c compilers), ffmpeg
    * explore auto-exposure setting, which is acting funky
    * more documentation
    * benchmarks, performance tests (including n_in n_out counts)
    * build a multithreaded cython option for camera streaming to free the main process
    * simultaneous display/saving?

Working notes for documentation:
* The PSEye camera has two LED indicators: a blue light indicating power, and a red light indiciating communication with the computer.
* If the cameras or API act strangely, try disconnecting and reconnecting the cameras, restarting the Python shell, and running the program again.
