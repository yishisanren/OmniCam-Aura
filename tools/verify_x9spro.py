"""Validate the port against the private stock snapshot and the final package."""
import copy
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from zipfile import ZipFile
from prepare_x9spro import ROOT, STOCK, MODULE, read_json, parse_wire

VERSION = '1.0.1-x9spro.1'
APK = ROOT / f'dist/OmniCam-Aura-{VERSION}.apk'
ZIP = ROOT / f'dist/OmniCam-Aura-{VERSION}-KSU.zip'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def fields(data):
    return {n: v for n, w, v in parse_wire(data)}


def modes(data):
    table = next(v for n, w, v in parse_wire(data) if n == 2)
    return {fields(entry)[1].decode(): fields(entry)[2]
            for _, _, entry in parse_wire(table)}


def check_configuration():
    original = read_json(STOCK / 'config/camera_unit_config')
    merged = read_json(MODULE / 'payload/camera_unit_config')
    expected = copy.deepcopy(original)
    for camera, values in expected['mode_type_list'].items():
        for new, base in [('gr_mode', 'professional_mode'), ('retro_camera_mode', 'photo_mode')]:
            if base in values:
                values.append(new)
    for new, base in [('gr_mode', 'professional_mode'), ('retro_camera_mode', 'photo_mode')]:
        expected['mode_operation_mode'][new] = original['mode_operation_mode'][base]
        if base in original['capture_stream_number']:
            expected['capture_stream_number'][new] = original['capture_stream_number'][base]
    for new, base in [('gr_mode_case', 'professional_case'), ('gr_mode_hq_raw_case', 'professional_hqraw_case'), ('retro_camera_case', 'sat_photo_case')]:
        expected['usecase_info'][new] = original['usecase_info'][base]
    require(merged == expected, 'Unexpected change in stock camera/sensor/session configuration')
    require(merged['device_info']['platform'] == 'mtk', 'Platform must remain MTK')

    stock_pb = (STOCK / 'config/camera_unit_feature_config.protobuf').read_bytes()
    port_pb = (MODULE / 'payload/camera_unit_feature_config.protobuf').read_bytes()
    old_pool = [v for n, w, v in parse_wire(stock_pb) if n == 1]
    pool = [v for n, w, v in parse_wire(port_pb) if n == 1]
    require(pool[:len(old_pool)] == old_pool, 'Original string indices changed')
    old_modes, new_modes = modes(stock_pb), modes(port_pb)
    require(set(new_modes) - set(old_modes) == {'gr_mode', 'retro_camera_mode'}, 'Unexpected added protobuf mode')
    require(all(new_modes[k] == v for k, v in old_modes.items() if k != 'high_pixel_mode'), 'Existing protobuf mode changed')
    highpixel_added = 0
    hp_added_nodes = []
    old_hp, new_hp = parse_wire(old_modes['high_pixel_mode']), parse_wire(new_modes['high_pixel_mode'])
    require(len(old_hp) == len(new_hp), 'High pixel camera table changed')
    for old, new in zip(old_hp, new_hp):
        require(old[:2] == new[:2], 'High pixel camera table wire changed')
        old_camera, new_camera = fields(old[2]), fields(new[2])
        require({k:v for k,v in old_camera.items() if k != 2} == {k:v for k,v in new_camera.items() if k != 2}, 'High pixel camera identity changed')
        before, after = parse_wire(old_camera[2]), parse_wire(new_camera[2])
        require(after[:len(before)] == before, 'Existing high pixel feature changed')
        additions = after[len(before):]
        if additions:
            require(pool[new_camera[1]] in {b'front_main', b'rear_main', b'rear_wide', b'rear_tele'}, 'Unsupported high pixel camera modified')
        for _, _, node in additions:
            feature = fields(node)
            require(pool[feature[1]] in {b'com.oplus.camera.feature.filter', b'com.oplus.camera.feature.beauty'}, 'Unrelated high pixel feature added')
            require(pool[feature[2]] in {b'feature_filter_index', b'com.oplus.camera.feature.beauty', b'beauty_change_by_ai_scene'}, 'Unrelated high pixel setting added')
            hp_added_nodes.append(node)
        highpixel_added += len(additions)
    require(highpixel_added == 8, 'Expected eight high pixel filter/beauty nodes')
    require([(n, w, v) for n, w, v in parse_wire(stock_pb) if n not in [1, 2]] ==
            [(n, w, v) for n, w, v in parse_wire(port_pb) if n not in [1, 2]], 'Other protobuf fields changed')

    count = 0
    def valid(index):
        require(isinstance(index, int) and 0 <= index < len(pool), 'Invalid protobuf string index')
    for name in ['gr_mode', 'retro_camera_mode']:
        for _, _, entry in parse_wire(new_modes[name]):
            camera = fields(entry)
            valid(camera[1])
            require(pool[camera[1]] != b'rear_ultra_tele', 'Ultra-only camera type leaked')
            for _, _, feature in parse_wire(camera[2]):
                count += 1
                for n, w, value in parse_wire(feature):
                    if 1 <= n <= 6:
                        valid(value)
                    elif n == 8:
                        conflict = fields(value)
                        valid(conflict.get(1, 0))
                        for _, _, item in parse_wire(conflict[2]):
                            for f, ww, index in parse_wire(item):
                                require(f in [1, 2, 3] and ww == 0, 'Unknown conflict schema')
                                valid(index)

    old_cfg = {r['VendorTag']: r for r in read_json(STOCK / 'oplus_camera_config.decoded.json')}
    cfg = {r['VendorTag']: r for r in read_json(MODULE / 'payload/oplus_camera_config')}
    allowed = set(read_json(MODULE / 'profile.json')['changed_config_keys'])
    changed = {k for k in old_cfg.keys() | cfg.keys() if old_cfg.get(k) != cfg.get(k)}
    require(changed <= allowed, 'Camera vendor configuration changed outside allowlist')
    require(cfg['com.oplus.available.gr.mode.zoomvalues']['Value'] == old_cfg['com.oplus.pro.zoom.marked.zoomvalues']['Value'], 'GR focal lengths do not match this phone')
    old_algo = read_json(STOCK / 'oplus_camera_algo_switch_config.decoded.json')
    expected_algo = copy.deepcopy(old_algo)
    for table in ['aps_capture_configs', 'aps_preview_configs']:
        index = {r['mode']: r for r in old_algo[table]}
        for new, base in [('retroCamera', 'common'), ('grmode', 'master')]:
            row = copy.deepcopy(index[base]); row['mode'] = new
            expected_algo[table].append(row)
        if table == 'aps_capture_configs':
            for row in expected_algo[table]:
                if row['mode'] in ['common', 'portrait', 'aiHighPixel']:
                    for camera in row['entity']:
                        if camera.get('enable') == 1:
                            camera['aps_algo_color_palette'] = 1
    require(read_json(MODULE / 'payload/oplus_camera_algo_switch_config') == expected_algo, 'Existing MTK algorithm pipeline changed')
    expected_aps = read_json(STOCK / 'oplus_camera_aps_config.decoded.json')
    expected_aps['file_data'].append({'VendorTag': 'com.oplus.color.palette.portrait.lut.weight', 'Type': 'Float', 'Count': '1', 'Value': '0.85'})
    require(read_json(MODULE / 'payload/oplus_camera_aps_config') == expected_aps, 'Original MTK APS parameters changed')
    require((MODULE / 'system/odm/lib64/libBasicTonePhotoX9.so').read_bytes() == (STOCK / 'libBasicTonePhoto.so').read_bytes(), 'X9 backend is not the phone original')
    for node in hp_added_nodes:
        for n,w,value in parse_wire(node):
            if 1 <= n <= 6:
                valid(value)
    return {'stock_protobuf_modes_preserved': len(old_modes), 'highpixel_features_added': highpixel_added, 'new_feature_indices_checked': count, 'changed_vendor_keys': sorted(changed)}


def check_package():
    sources = json.loads((MODULE / 'payload/gr-lut-sources.json').read_text())
    require({row['file'] for row in sources} == {'gr.bw.rgba.bin', 'gr.hi.bw.rgba.bin', 'gr.nega.rgba.bin', 'gr.posi.rgba.bin'}, 'GR style asset missing')
    for row in sources:
        data = (MODULE / 'payload/meishe_lut' / row['file']).read_bytes()
        require(len(data) == row['size'] and hashlib.sha256(data).hexdigest() == row['sha256'], 'GR style asset checksum mismatch')
        require(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == row['git_blob'], 'GR asset differs from source Git blob')
    sdk = Path(os.environ['ANDROID_HOME'])
    build_tools = next(p for p in sorted((sdk / 'build-tools').iterdir(), reverse=True) if (p / 'aapt2').exists())
    with ZipFile(ZIP) as bundle, ZipFile(APK) as apk:
        require(bundle.testzip() is None and apk.testzip() is None, 'ZIP/APK CRC failed')
        names = bundle.namelist()
        require('skip_mount' in names and 'restore-resources.sh' in names and 'uninstall.sh' in names, 'Guard/recovery files missing')
        apk_names = [n for n in names if n.endswith('.apk')]
        require(len(apk_names) == 1 and bundle.read(apk_names[0]) == APK.read_bytes(), 'Module APK differs from verified APK')
        forbidden = ['system/odm/lib64/libAlgoInterface.so', 'payload/isp/', 'payload/gamma/']
        require(not any(n.startswith(prefix) for n in names for prefix in forbidden), 'Unsafe donor ISP/AlgoInterface overlay')
        for name in ['libBasicTonePhoto.so', 'libBasicTonePhotoX9.so', 'libBasicTonePhotoX10.so', 'libmsnativefilter.so']:
            require('system/odm/lib64/' + name in names, 'Backend missing: ' + name)
        for path in MODULE.rglob('*'):
            if path.is_file():
                require(bundle.read(path.relative_to(MODULE).as_posix()) == path.read_bytes(), 'Stale packaged file')
        require(apk.read('assets/xposed_init').strip() == b'local.omnicam.aura.ModuleEntry', 'Wrong Xposed entry')
        require(apk.read('assets/native_init').strip() == b'libaura_native.so', 'Wrong native entry')
        require('lib/arm64-v8a/libaura_native.so' in apk.namelist(), 'Native Hook absent')
    manifest = subprocess.check_output([str(build_tools / 'aapt2'), 'dump', 'xmltree', str(APK), '--file', 'AndroidManifest.xml'], text=True)
    badging = subprocess.check_output([str(build_tools / 'aapt2'), 'dump', 'badging', str(APK)], text=True)
    require("name='local.omnicam.aura'" in badging and f"versionName='{VERSION}'" in badging, 'Wrong package/version')
    for component in ['activity ', 'activity-alias ', 'provider ', 'service ', 'receiver ']:
        require('E: ' + component not in manifest, 'Unexpected APK component')
    scope = (ROOT / 'app/src/main/res/values/arrays.xml').read_text()
    require('com.oplus.camera' in scope and 'com.coloros.gallery3d' in scope and '<item>android</item>' not in scope, 'Wrong LSPosed scope')
    resources = subprocess.check_output([str(build_tools / 'aapt2'), 'dump', 'resources', str(APK)], text=True)
    for name in ['snap_switch_on', 'snap_switch_off', 'snap_switch_1m', 'snap_switch_2_5m', 'snap_switch_5m']:
        require('drawable/' + name in resources, 'GR focus resource stripped: ' + name)
    subprocess.run([str(build_tools / 'apksigner'), 'verify', '--verbose', str(APK)], check=True)
    for script in MODULE.glob('*.sh'):
        subprocess.run(['sh', '-n', str(script)], check=True)
    service = (MODULE / 'service.sh').read_text()
    require('set_config' not in service and 'shared_prefs' not in service, 'Persistent camera preferences altered')
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [APK, ZIP]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package-only', action='store_true', help='Validate the package without the private stock snapshot; does not validate stock configuration preservation')
    args = parser.parse_args()
    configuration = {'status': 'not run', 'reason': 'private stock snapshot not used (--package-only)'} if args.package_only else check_configuration()
    result = {'configuration': configuration, 'packages': check_package(), 'device_tests': 'not run by static verifier; see evidence/device-acceptance.json'}
    (ROOT / 'evidence').mkdir(exist_ok=True)
    (ROOT / 'evidence/static-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
