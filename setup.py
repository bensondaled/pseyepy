from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
from sysconfig import get_paths
import os, sys
import warnings
import subprocess

### install libusb
# keeping this slightly hacky approach to guarantee that the correct libusb is used and is easily findable
if sys.platform in ('darwin','linux','linux2'):
    python_data_path = get_paths()['data']

    wd = os.path.join('.','pseyepy','ext')
    subprocess.call('tar -jxf libusb-1.0.21.tar.bz2', cwd=wd, shell=True)

    wd = os.path.join('.','pseyepy','ext','libusb-1.0.21')
    subprocess.call('sudo ./configure --prefix={}'.format(python_data_path), cwd=wd, shell=True)
    subprocess.call('make clean', cwd=wd, shell=True)
    subprocess.call('sudo make', cwd=wd, shell=True)
    subprocess.call('sudo make install', cwd=wd, shell=True)

    wd = os.path.join('.','pseyepy','ext')
    subprocess.call('mkdir -p include && mkdir -p lib', cwd=wd, shell=True)

    src_include = os.path.join(python_data_path, 'include', 'libusb-1.0')
    dest_include = os.path.join('.', 'pseyepy', 'ext', 'include', 'libusb-1.0')
    subprocess.call(['ln -s {} {}'.format(src_include, dest_include)], shell=True, cwd='.')

    for ln in ['libusb-1.0.0.dylib', 'libusb-1.0.a', 'libusb-1.0.dylib', 'libusb-1.0.la']:
        src_lib = os.path.join(python_data_path, 'lib', ln)
        dest_lib = os.path.join('.', 'pseyepy', 'ext', 'lib', ln)
        subprocess.call(['ln -s {} {}'.format(src_lib, dest_lib)], shell=True, cwd='.')

    libusb_incl = ['pseyepy/ext/include/libusb-1.0']
    libusb_libpath = 'pseyepy/ext/lib'
    libs = ['usb-1.0']

elif sys.platform.startswith('win'):
    # precompiled library from:
    # https://sourceforge.net/projects/libusb/files/libusb-1.0/libusb-1.0.21/libusb-1.0.21.7z/download
    # need visualstudio prior to 2013, for this precompiled library
    # therefore ideally before even python installation, install vs
    # currently used link i have to vs2012, but could use older 2008 at http://download.microsoft.com/download/A/5/4/A54BADB6-9C3F-478D-8657-93B3FC9FE62D/vcsetup.exe
    # if setup.py still appears to be using a newer version, can hack it:
    # https://www.ibm.com/developerworks/community/blogs/jfp/entry/Installing_Cython_On_Anaconda_On_Windows?lang=en
    # https://sleangao.wordpress.com/2015/03/24/using-cython-under-windows-7-with-msvc-compiler/
    warnings.warn('Setup params not yet fully tested for Windows.')

    libusb_incl = [os.path.join('pseyepy', 'ext', 'win', 'include', 'libusb-1.0')]
    libusb_libpath = 'pseyepy/ext/win/lib'
    libs = ['libusb-1.0']

### setup params
os.environ["CC"]= "g++"
srcs = ['pseyepy/src/ps3eye.cpp','pseyepy/src/ps3eye_capi.cpp','pseyepy/cameras.pyx']
extensions = [  Extension('pseyepy.cameras',
                srcs, 
                language='c++',
                extra_compile_args=['-std=c++11','-stdlib=libc++'],
                extra_link_args=['-std=c++11','-stdlib=libc++'],
                include_dirs=['pseyepy/src']+libusb_incl,
                library_dirs=[libusb_libpath],
                libraries=libs,
            )]

### run setup
setup(  name='pseyepy',
        version='0.0',
        description='pseyepy camera package',
        author='Ben Deverett',
        author_email='deverett@princeton.edu',
        url='https://github.com/bensondaled/pseyepy',
        packages=['pseyepy'],
        package_data={'pseyepy': ['cameras.pyx']},
        ext_modules=cythonize(extensions),)
