"""Record only media created during an explicitly named device test."""
import json
import pathlib
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET
from device_actions import ADB, touch


def recent(kind, start):
    uri = 'content://media/external/' + ('video' if kind == 'video' else 'images') + '/media'
    projection = '_id:_display_name:_data:width:height:date_added'
    if kind == 'video':
        projection += ':duration'
    args = ['content', 'query', '--uri', uri, '--projection', projection, '--where', f'date_added>={start}']
    result = subprocess.check_output(ADB + ['shell', shlex.join(args)], text=True)
    rows = []
    for line in result.splitlines():
        if not line.startswith('Row: '):
            continue
        fields = line.split(' ', 2)[2]
        rows.append(dict(pair.split('=', 1) for pair in fields.split(', ')))
    return rows


def capture(name, kind='photo', expected_mode=None, expected_style=None, video_duration=5):
    if kind == 'video' and not 1 <= video_duration <= 60:
        raise ValueError('Video test duration must be between 1 and 60 seconds')
    subprocess.run(ADB + ['shell', 'uiautomator', 'dump', '/data/local/tmp/aura-capture-ui.xml'], check=True, stdout=subprocess.DEVNULL)
    xml = subprocess.check_output(ADB + ['shell', 'cat', '/data/local/tmp/aura-capture-ui.xml'], text=True)
    pathlib.Path('evidence', name + '-before.xml').write_text(xml)
    nodes = list(ET.fromstring(xml).iter('node'))
    if any(n.get('resource-id') == 'com.oplus.camera:id/top_expand_touch_mask' for n in nodes):
        raise RuntimeError(f'{name}: close the expanded top menu before capture')
    mode = next((n.get('content-desc') for n in nodes if n.get('resource-id') == 'com.oplus.camera:id/headline_view'), '')
    if expected_mode is None:
        expected_mode = '理光 GR' if name.startswith('gr-') else 'POP' if name.startswith('pop-') else None
    if expected_mode and expected_mode not in mode:
        raise RuntimeError(f'{name}: expected {expected_mode}, current {mode}')
    style = next((n.get('text') for n in nodes if n.get('resource-id') == 'com.oplus.camera:id/master_effect_menu_soft_light_value_text'), '')
    if expected_style and style != expected_style:
        raise RuntimeError(f'{name}: expected style {expected_style}, current {style}')
    start = int(subprocess.check_output(ADB + ['shell', 'date +%s'], text=True))
    touch('com.oplus.camera', 'tap', 608, 2155)
    if kind == 'video':
        checkpoint = min(5, video_duration)
        time.sleep(checkpoint)
        pathlib.Path('evidence', name + '-recording.png').write_bytes(
            subprocess.check_output(ADB + ['exec-out', 'screencap', '-p']))
        time.sleep(max(0, video_duration - checkpoint))
        touch('com.oplus.camera', 'tap', 608, 2155)
    for _ in range(10):
        time.sleep(2)
        rows = recent(kind, start)
        if rows:
            break
    if not rows:
        raise RuntimeError(f'{name}: no saved {kind}')
    result = {'case': name, 'kind': kind, 'mode': mode, 'style': style, 'start': start, 'media': rows}
    if kind == 'video':
        result['requested_recording_seconds'] = video_duration
    path = pathlib.Path('evidence') / (name + '-media.json')
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == '__main__':
    import sys
    capture(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'photo', sys.argv[3] if len(sys.argv) > 3 else None, sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else None, float(sys.argv[5]) if len(sys.argv) > 5 else 5)
