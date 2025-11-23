import os
import sys

# On Windows, register any packaged DLL directory so the OS loader can find
# third-party DLLs (libusb). Prefer `os.add_dll_directory` (Python 3.8+).
if sys.platform == 'win32':
	try:
		pkg_dir = os.path.dirname(__file__)

		# Search locations in priority order:
		# 1. _libs/ - installed package location
		# 2. ext/win/lib/ - development/build location
		dll_dirs = [
			os.path.join(pkg_dir, '_libs'),
			os.path.join(pkg_dir, 'ext', 'win', 'lib')
		]

		for dll_dir in dll_dirs:
			if os.path.isdir(dll_dir):
				try:
					os.add_dll_directory(dll_dir)
				except Exception:
					# Fallback for older Pythons: prepend to PATH
					os.environ['PATH'] = dll_dir + os.pathsep + os.environ.get('PATH', '')
				# Stop after registering the first valid directory
				break
	except Exception:
		# Don't fail import just because DLL path setup failed
		pass

from .cameras import Camera, cam_count
from .ui import Display
from .io import Stream
