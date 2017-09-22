from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
import os
import subprocess

# python setup.py build_ext --inplace

os.environ["CC"]= "g++"
libusb_incl = subprocess.check_output(['pkg-config', '--cflags', 'libusb-1.0']).strip().decode('utf8')
libusb_incl = libusb_incl.replace('-I','')
libusb_incl = libusb_incl.split(' ')

srcs = ['pseyepy/src/ps3eye.cpp','pseyepy/src/ps3eye_capi.cpp','pseyepy/cameras.pyx']

extensions = [Extension('pseyepy.cameras',  # I think this will be pseyepy.pseyepy.cameras when I don't build inplace
    srcs, 
    language='c++',
    extra_compile_args=['-std=c++11','-stdlib=libc++'],
    extra_link_args=['-std=c++11','-stdlib=libc++'],
    include_dirs=['pseyepy/src']+libusb_incl,
    libraries=['usb'],
    )]

setup(ext_modules=
        cythonize(extensions),
        )
