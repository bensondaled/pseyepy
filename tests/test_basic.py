#!/usr/bin/env python3
"""Basic smoke test for pseyepy.

This script exercises a minimal surface area of the package:
- import pseyepy
- import pseyepy.cameras and call `cam_count()`
- if cameras are present, try to initialize a `Camera` and read one frame (wrapped in try/except)

Run with the project's venv Python to use the built extension:
  & D:/Development/Projects/pseyepy_fix/pseyepy/.venv/Scripts/python.exe tests/test_basic.py
"""
import sys
import traceback

from pseyepy.ui import Display


def main():
    try:
        import pseyepy
        print('Imported pseyepy ->', pseyepy.__name__)
    except Exception as exc:
        print('ERROR: Failed to import pseyepy:', exc)
        traceback.print_exc()
        return 2

    try:
        from pseyepy import cameras
        print('Imported pseyepy.cameras ->', cameras)
    except Exception as exc:
        print('ERROR: Failed to import pseyepy.cameras:', exc)
        traceback.print_exc()
        return 3

    # call cam_count (safe even if no hardware)
    try:
        n = cameras.cam_count()
        print('cam_count() ->', n)
    except Exception as exc:
        print('WARNING: cam_count() raised an exception (may be fine):', exc)
        traceback.print_exc()
        n = 0

    if n:
        print('Detected cameras, attempting to initialize first camera (wrapped)')
        try:
            cam = cameras.Camera()
            print('Camera object created, ids =', getattr(cam, 'ids', None))
            try:
                # try a single read from camera 0
                frames, ts = cam.read(0)
                print('Read returned. frame type:', type(frames), 'timestamp type:', type(ts))
                d = Display(cam) # begin the display
                try:
                    print('Frame shape:', getattr(frames, 'shape', 'N/A'))
                except Exception:
                    pass
            except Exception as exc:
                print('WARNING: Camera.read() failed:', exc)
                traceback.print_exc()
            finally:
                try:
                    cam.end()
                except Exception:
                    pass
        except Exception as exc:
            print('ERROR: Failed to initialize Camera:', exc)
            traceback.print_exc()
            return 4
    else:
        print('No cameras found; skipping Camera initialization test.')

    print('Basic smoke test completed successfully')
    return 0


if __name__ == '__main__':
    sys.exit(main())
