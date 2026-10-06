"""Read back this device's final files and LSPosed scope after reboot."""
import hashlib
import io
import json
from pathlib import Path
import shlex
import sqlite3
import subprocess
import tarfile
from device_actions import ADB

ROOT = Path(__file__).resolve().parent.parent
MOD = '/data/adb/modules/omnicam_aura_x9spro'


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
    for path in [ROOT / 'dist/OmniCam-Aura-1.0.1-x9spro.1.apk', ROOT / 'module/profile.json']:
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        actual = root('sha256sum ' + MOD + '/' + path.name).split()[0]
        assert actual == expected, path.name
    apk = subprocess.check_output(ADB + ['shell', 'pm', 'path', 'local.omnicam.aura'], text=True).strip()[8:]
    actual = root('sha256sum ' + shlex.quote(apk)).split()[0]
    assert actual == hashlib.sha256((ROOT / 'dist/OmniCam-Aura-1.0.1-x9spro.1.apk').read_bytes()).hexdigest()
    result['installed_apk_sha256'] = actual
    assert root('sha256sum /odm/lib64/libAlgoInterface.so').split()[0] == json.loads(
        (ROOT / 'module/profile.json').read_text())['algo_sha256']
    rules = root('/data/adb/modules/nomount/bin/nm rule list')
    for name in ['libBasicTonePhoto.so', 'libBasicTonePhotoX9.so', 'libBasicTonePhotoX10.so', 'libmsnativefilter.so']:
        assert any('/odm/lib64/' + name + ' -> ' in line and MOD in line for line in rules.splitlines()), name
    result['native_library_redirects'] = 4
    bind = root('cat ' + MOD + '/bind.log')
    assert bind.count('file bind ok') == 5 and bind.count('dir bind ok') == 2 and 'FAIL' not in bind
    result['configuration_mounts'] = 5
    result['resource_directory_mounts'] = 2
    stage = root('cat ' + MOD + '/stage.log')
    assert 'Resource staging complete' in stage
    assert root('test -f /data/adb/omnicam_aura_x9spro_backup/ready; echo $?').strip() == '0'
    snapshot = root('tar -cf - -C /data/adb/lspd/config modules_config.db modules_config.db-wal modules_config.db-shm', True)
    dest = ROOT / 'evidence/lspd-final'
    dest.mkdir(exist_ok=True)
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
    baseline = sqlite3.connect(str(ROOT / 'evidence/lspd-pre-install/modules_config.db'))
    for table in ['modules_state', 'scope']:
        query = f'select * from {table} where module_pkg_name<>?'
        assert set(conn.execute(query, [own])) == set(baseline.execute(query, [own])), table
    result['lsposed_enabled'] = True
    result['scope'] = [row[0] for row in scope]
    result['other_lsposed_state_preserved'] = True
    (ROOT / 'evidence/final-device-files.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    verify()
