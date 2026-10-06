"""Navigate this test phone one observed camera mode at a time."""
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from device_actions import ADB, touch

ORDER = ['专业', '视频', '照片', '人像', '哈苏超清', 'POP', '理光 GR', '更多']


def current():
    subprocess.run(ADB + ['shell', 'uiautomator', 'dump', '/data/local/tmp/aura-mode.xml'],
                   check=True, stdout=subprocess.DEVNULL)
    xml = subprocess.check_output(ADB + ['shell', 'cat', '/data/local/tmp/aura-mode.xml'])
    nodes = list(ET.fromstring(xml).iter('node'))
    if any(n.get('resource-id') == 'com.oplus.camera:id/top_expand_touch_mask' for n in nodes):
        raise RuntimeError('Close the expanded camera menu first')
    desc = next((n.get('content-desc', '') for n in nodes
                 if n.get('resource-id') == 'com.oplus.camera:id/headline_view'), '')
    return next((v for v in ORDER if desc.startswith(v + '模式')), None)


def select(target):
    if target not in ORDER:
        raise ValueError(target)
    for _ in range(12):
        mode = current()
        if mode == target:
            print('Verified camera mode:', target)
            return
        if mode is None:
            raise RuntimeError('Camera mode not observable; close settings/filter panels')
        delta = 170 if ORDER.index(mode) > ORDER.index(target) else -170
        touch('com.oplus.camera', 'swipe', 608, 2440, 608 + delta, 2440, 300)
        time.sleep(2)
    raise RuntimeError('Camera did not reach the requested mode')


if __name__ == '__main__':
    select(sys.argv[1])
