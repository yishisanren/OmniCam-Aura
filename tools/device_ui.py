"""Save only the connected test phone's current UI and screenshot."""
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
from device_actions import ADB

ROOT = Path(__file__).resolve().parent.parent
name = sys.argv[1]
output = ROOT / 'evidence' / name
subprocess.run(ADB + ['shell', 'uiautomator', 'dump', '/data/local/tmp/aura-ui.xml'], check=True, stdout=subprocess.DEVNULL)
xml = subprocess.check_output(ADB + ['exec-out', 'cat', '/data/local/tmp/aura-ui.xml'])
output.with_suffix('.xml').write_bytes(xml)
output.with_suffix('.png').write_bytes(subprocess.check_output(ADB + ['exec-out', 'screencap', '-p']))
tree = ET.fromstring(xml)
for node in tree.iter('node'):
    if node.get('text') or node.get('content-desc') or node.get('clickable') == 'true':
        print(node.get('text'), node.get('content-desc'), node.get('resource-id'), node.get('bounds'))
