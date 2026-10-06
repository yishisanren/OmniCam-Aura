"""Guard touch input against another app taking over the shared test phone."""
import os
import shutil
import subprocess
import sys

DEVICE_SERIAL = os.environ.get('AURA_DEVICE_SERIAL')
if not DEVICE_SERIAL:
    raise RuntimeError('Set AURA_DEVICE_SERIAL to the intended test device serial')
ADB = [shutil.which('adb') or 'adb', '-s', DEVICE_SERIAL]


def foreground():
    window = subprocess.check_output(ADB + ['shell', 'dumpsys', 'window'], text=True)
    return next((line.strip() for line in window.splitlines() if 'mCurrentFocus=' in line), '')


def touch(package, action, *arguments):
    focus = foreground()
    if f' {package}/' not in focus:
        raise RuntimeError(f'Touch cancelled: expected {package}, current {focus}')
    if action not in ['tap', 'swipe', 'keyevent', 'text']:
        raise ValueError(action)
    subprocess.run(ADB + ['shell', 'input', action, *map(str, arguments)], check=True)


if __name__ == '__main__':
    touch(sys.argv[1], sys.argv[2], *sys.argv[3:])
