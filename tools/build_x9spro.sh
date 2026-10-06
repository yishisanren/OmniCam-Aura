#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
: "${ANDROID_HOME:?Set ANDROID_HOME to the Android SDK}"
: "${JAVA_HOME:?Set JAVA_HOME to JDK 21 or later}"
export GRADLE_USER_HOME="${GRADLE_USER_HOME:-$PWD/tools/gradle-home}"
OMNICAM_BUILD_DIR=${OMNICAM_BUILD_DIR:-$HOME/.cache/omnicam-aura-x9spro-build}
./gradlew --no-daemon "-PauraBuildDir=$OMNICAM_BUILD_DIR" :app:assembleRelease :app:lintRelease
mkdir -p dist
APK=OmniCam-Aura-1.0.1-x9spro.1.apk
cp "$OMNICAM_BUILD_DIR/outputs/apk/release/app-release.apk" "dist/$APK"
cp "dist/$APK" "module/$APK"
python3 tools/zip_module.py module dist/OmniCam-Aura-1.0.1-x9spro.1-KSU.zip
if [ -f evidence/original/config/camera_unit_config ]; then
    python3 tools/verify_x9spro.py
else
    echo 'Private stock snapshot absent: package checks only; stock configuration preservation and device behavior are not verified.'
    python3 tools/verify_x9spro.py --package-only
fi
