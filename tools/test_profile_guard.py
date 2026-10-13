"""Exercise the actual boot guard before PackageManager is available."""
import json
from pathlib import Path
import shlex
import subprocess

root = Path(__file__).resolve().parent.parent
profile = json.loads((root / 'module/profile.json').read_text())
guard = root / 'module/device-profile.sh'
prefix = f'''
. {shlex.quote(str(guard))}
getprop() {{
    case "$1" in
        ro.product.model) echo "$TEST_MODEL" ;;
        ro.build.display.id) echo "$TEST_FIRMWARE" ;;
        *) return 1 ;;
    esac
}}
sha256sum() {{
    case "$1" in
        /product/app/OplusCamera/OplusCamera.apk) echo "$TEST_CAMERA  $1" ;;
        /odm/lib64/libAlgoInterface.so) echo "$TEST_ALGO  $1" ;;
        *) return 1 ;;
    esac
}}
pm() {{ echo 'PackageManager is unavailable at post-fs-data' >&2; return 99; }}
'''
base = {'TEST_MODEL': profile['model'], 'TEST_FIRMWARE': profile['firmware'],
        'TEST_CAMERA': profile['apk_sha256'], 'TEST_ALGO': profile['algo_sha256']}
cases = [('matching device before PackageManager starts', {}, True),
         ('different model', {'TEST_MODEL': 'OTHER'}, False),
         ('different firmware', {'TEST_FIRMWARE': 'OTHER'}, False),
         ('different camera APK', {'TEST_CAMERA': '0' * 64}, False),
         ('different algorithm library', {'TEST_ALGO': '0' * 64}, False)]
for name, changes, accepted in cases:
    values = dict(base, **changes)
    assignments = '\n'.join(k + '=' + shlex.quote(v) for k, v in values.items())
    result = subprocess.run(['sh', '-c', prefix + assignments + '\naura_device_matches'], capture_output=True, text=True)
    assert (result.returncode == 0) == accepted, (name, result.stderr)
    assert not result.stderr, (name, result.stderr)
    print('Passed:', name)
