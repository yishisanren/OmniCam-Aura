"""Exercise the actual service query block with Binder-like stderr rejection."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
source = (ROOT / 'module/service.sh').read_text()
block = source[source.index('if ! CAMERA_PATH='):source.index('APP_UID=')]

with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    pm = temp / 'pm'
    pm.write_text('#!' + sys.executable + '\n' + '''
import os, stat, sys
if stat.S_ISREG(os.fstat(2).st_mode) or os.environ['PM_CASE'] == 'failure':
    print('cmd: Failure calling service package: Failed transaction (2147483646)')
    sys.exit(2)
print('package:' + ('/data/app/updated-camera.apk' if os.environ['PM_CASE'] == 'update'
                   else '/product/app/OplusCamera/OplusCamera.apk'))
''')
    pm.chmod(0o755)
    for case, expected_code, expected_success in [
        ('stock', 0, True), ('failure', 1, False), ('update', 0, False)
    ]:
        log = temp / (case + '.log')
        script = 'set -eu\nexec >>"' + str(log) + '" 2>&1\n' + block + '\necho query-passed\n'
        env = dict(os.environ, PATH=str(temp) + os.pathsep + os.environ['PATH'], PM_CASE=case)
        result = subprocess.run(['sh', '-c', script], env=env)
        output = log.read_text()
        assert result.returncode == expected_code, (case, output)
        assert ('query-passed' in output) == expected_success, (case, output)
        print(case + ': passed')
