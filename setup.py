from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
import os, sys
import warnings
import subprocess


if sys.platform in ('darwin','linux','linux2'):
    libusb_incl = subprocess.check_output(['pkg-config', '--cflags', 'libusb-1.0']).strip().decode('utf8')
    libusb_incl = libusb_incl.replace('-I','').split(' ')

    libusb_libpath = subprocess.check_output(['pkg-config', '--libs', 'libusb-1.0']).strip().decode('utf8')
    libusb_libpath = libusb_libpath.replace('-L','').split(' ')[0] # 0 for path, b/c second item is often the library itself; this is a bit hacky

elif sys.platform.startswith('win'):
    warnings.warn('Setup params not yet configured for Windows. Setup will only work if libusb library paths are automatically found.')

os.environ["CC"]= "g++"

srcs = ['pseyepy/src/ps3eye.cpp','pseyepy/src/ps3eye_capi.cpp','pseyepy/cameras.pyx']

extensions = [  Extension('pseyepy.cameras',  # I think this will be pseyepy.pseyepy.cameras when I don't build inplace
                srcs, 
                language='c++',
                extra_compile_args=['-std=c++11','-stdlib=libc++'],
                extra_link_args=['-std=c++11','-stdlib=libc++'],
                include_dirs=['pseyepy/src']+libusb_incl,
                library_dirs=[libusb_libpath],
                libraries=['usb'],
            )]

setup(ext_modules=cythonize(extensions),)
