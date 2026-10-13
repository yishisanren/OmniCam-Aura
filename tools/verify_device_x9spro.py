"""Read back this device's final files and LSPosed scope after reboot."""
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import sqlite3
import subprocess
import tarfile
from device_actions import ADB

ROOT = Path(__file__).resolve().parent.parent
MOD = '/data/adb/modules/omnicam_aura_x9spro'
EVIDENCE = Path(os.environ.get('AURA_EVIDENCE_DIR', ROOT / 'evidence'))
LSPOSED_BASELINE = Path(os.environ.get('AURA_LSPOSED_BASELINE', EVIDENCE / 'lspd-pre-install'))


def root(command, binary=False):
    return subprocess.check_output(ADB + ['exec-out' if binary else 'shell',
        shlex.join(['su', '-c', command])], text=not binary)


def verify():
    result = {'file_hashes': {}, 'ce_available': subprocess.check_output(
        ADB + ['shell', 'getprop', 'sys.user.0.ce_available'], text=True).strip() == 'true'}
    assert result['ce_available'], 'Unlock required'
    for name in ['camera_unit_config', 'camera_unit_feature_config.protobuf', 'oplus_camera_config',
                 'oplus_camera_algo_switch_config', 'oplus_camera_aps_config']:
        expected = hashlib.sha256((ROOT / 'module/payload' / name).read_bytes()).hexdigest()
        actual = root('sha256sum /odm/etc/camera/config/' + name).split()[0]
        assert actual == expected, name
        result['file_hashes'][name] = actual
    version = next(line.split('=', 1)[1] for line in (ROOT / 'module/module.prop').read_text().splitlines() if line.startswith('version='))
    artifact = ROOT / f'dist/OmniCam-Aura-{version}.apk'
    for path in [artifact, ROOT / 'module/profile.json']:
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        actual = root('sha256sum ' + MOD + '/' + path.name).split()[0]
        assert actual == expected, path.name
    apk = subprocess.check_output(ADB + ['shell', 'pm', 'path', 'local.omnicam.aura'], text=True).strip()[8:]
    actual = root('sha256sum ' + shlex.quote(apk)).split()[0]
    assert actual == hashlib.sha256(artifact.read_bytes()).hexdigest()
    result['installed_apk_sha256'] = actual
    assert root('sha256sum /odm/lib64/libAlgoInterface.so').split()[0] == json.loads(
        (ROOT / 'module/profile.json').read_text())['algo_sha256']
    profile = json.loads((ROOT / 'module/profile.json').read_text())
    for path, expected in profile['mounted_files'].items():
        assert root('sha256sum ' + shlex.quote(path)).split()[0] == expected, path
    libraries = root('cat ' + MOD + '/libraries.log')
    if 'library overlay ok /odm/lib64' in libraries:
        result['native_library_backend'] = 'guarded read-only overlay'
    else:
        rules = root('/data/adb/modules/nomount/bin/nm rule list')
        for name in ['libBasicTonePhoto.so', 'libBasicTonePhotoX9.so', 'libBasicTonePhotoX10.so', 'libmsnativefilter.so']:
            assert any('/odm/lib64/' + name + ' -> ' in line and MOD in line for line in rules.splitlines()), name
        result['native_library_backend'] = 'NoMount'
    result['native_libraries_verified'] = 4
    bind = root('cat ' + MOD + '/bind.log')
    overlays = all('camera overlay ok /odm/etc/camera/' + name in libraries
        for name in ['config', 'meishe_lut', 'basictone'])
    if overlays:
        result['camera_overlay_directories'] = 4
    else:
        assert bind.count('file bind ok') == 5 and bind.count('dir bind ok') == 2 and 'FAIL' not in bind
    result['configuration_mounts'] = 5
    result['resource_directory_mounts'] = 2
    stage = root('cat ' + MOD + '/stage.log')
    assert 'Resource staging complete' in stage
    assert root('cat /data/user/0/com.oplus.camera/files/ricoh_gr/aura_profile.sha256').strip() == hashlib.sha256((ROOT / 'module/profile.json').read_bytes()).hexdigest()
    assert root('test -f /data/adb/omnicam_aura_x9spro_backup/ready; echo $?').strip() == '0'
    # A root-shell mount view can differ from the camera's view on Mountify.
    pid = root('pidof com.oplus.camera').strip()
    assert pid.isdigit(), 'Start the camera before runtime verification'
    camera_root = '/proc/' + pid + '/root'
    for path, expected in profile['mounted_files'].items():
        assert root('sha256sum ' + shlex.quote(camera_root + path)).split()[0] == expected, 'camera namespace: ' + path
    result['camera_namespace_files_verified'] = len(profile['mounted_files'])
    if overlays:
        mounts = root('cat /proc/' + pid + '/mountinfo').splitlines()
        for target in ['/odm/lib64', '/odm/etc/camera/config', '/odm/etc/camera/meishe_lut', '/odm/etc/camera/basictone']:
            assert any(line.split()[4] == target and 'ro' in line.split()[5].split(',')
                and line.split()[line.split().index('-') + 1] == 'overlay' for line in mounts), target
        result['camera_overlays_read_only'] = True
    for script in ['post-fs-data.sh', 'post-mount.sh', 'service.sh', 'device-profile.sh']:
        assert root('sha256sum ' + MOD + '/' + script).split()[0] == hashlib.sha256((ROOT / 'module' / script).read_bytes()).hexdigest(), script
    snapshot = root('tar -cf - -C /data/adb/lspd/config modules_config.db modules_config.db-wal modules_config.db-shm', True)
    dest = EVIDENCE / 'lspd-final'
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(snapshot)) as archive:
        for member in archive:
            assert member.name in ['modules_config.db', 'modules_config.db-wal', 'modules_config.db-shm']
            (dest / member.name).write_bytes(archive.extractfile(member).read())
    conn = sqlite3.connect(str(dest / 'modules_config.db'))
    assert conn.execute('pragma integrity_check').fetchone()[0] == 'ok'
    own = 'local.omnicam.aura'
    assert conn.execute('select enabled from modules_state where module_pkg_name=? and user_id=0', [own]).fetchone() == (1,)
    scope = conn.execute('select app_pkg_name, user_id from scope where module_pkg_name=?', [own]).fetchall()
    assert set(scope) == {('com.oplus.camera', 0), ('com.coloros.gallery3d', 0)}
    baseline = sqlite3.connect(str(LSPOSED_BASELINE / 'modules_config.db'))
    for table in ['modules_state', 'scope']:
        query = f'select * from {table} where module_pkg_name<>?'
        assert set(conn.execute(query, [own])) == set(baseline.execute(query, [own])), table
    result['lsposed_enabled'] = True
    result['scope'] = [row[0] for row in scope]
    result['other_lsposed_state_preserved'] = True
    (EVIDENCE / 'final-device-files.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify()
