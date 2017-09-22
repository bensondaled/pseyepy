from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
import os

# python setup.py build_ext --inplace

os.environ["CC"]= "g++"

srcs = ['pseyepy/src/ps3eye.cpp','pseyepy/src/ps3eye_capi.cpp','pseyepy/cameras.pyx']

extensions = [Extension('pseyepy.cameras', 
    srcs, 
    language='c++',
    extra_compile_args=['-std=c++11','-stdlib=libc++'],
    extra_link_args=['-std=c++11','-stdlib=libc++'],
    include_dirs=['/usr/local/Cellar/libusb/1.0.21/include/libusb-1.0','pseyepy/src'],
    libraries=['usb'],
    )]

setup(ext_modules=
        cythonize(extensions),
        )
