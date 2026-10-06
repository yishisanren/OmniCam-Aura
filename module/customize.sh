#!/system/bin/sh
# Installation is limited to the firmware actually inspected for this port.
MODEL=$(getprop ro.product.model)
FIRMWARE=$(getprop ro.build.display.id)
[ "$MODEL" = PME110 ] || abort "This package is only for PME110 (Find X9s Pro)."
[ "$FIRMWARE" = 'PME110_17.0.0.102(CN01)' ] || abort "Firmware has changed; revalidate the camera before installing."
ALGO=$(sha256sum /odm/lib64/libAlgoInterface.so | cut -d ' ' -f 1)
[ "$ALGO" = 8e6ce18cefae51089b8318970daea3087fb6434fed42d55810bf7456df8d66e5 ] || abort "Original MTK AlgoInterface does not match."
CAMERA=$(sha256sum /product/app/OplusCamera/OplusCamera.apk | cut -d ' ' -f 1)
[ "$CAMERA" = b85fed9ae429fc70034b6b6bd81101f40d503d7f5448b14fc305258837bb16a0 ] || abort "Camera APK is not the inspected 7.006.105 build."
[ "$(pm path com.oplus.camera)" = 'package:/product/app/OplusCamera/OplusCamera.apk' ] || abort "The active camera is a different update; revalidate it first."
[ -x /data/adb/modules/nomount/bin/nm ] && [ ! -e /data/adb/modules/nomount/disable ] || abort "This port requires the active NoMount metamodule."
for OTHER in /data/adb/modules/omnicam_aura /data/adb/modules/omnicam_muse; do
    if [ -d "$OTHER" ] && [ ! -e "$OTHER/disable" ] && [ ! -e "$OTHER/remove" ]; then
        abort "Disable the other OmniCam module first."
    fi
done
ui_print "PME110 / original MTK libraries verified."
set_perm_recursive "$MODPATH" 0 0 0755 0644
for SCRIPT in customize.sh post-fs-data.sh post-mount.sh service.sh uninstall.sh restore-resources.sh; do
    set_perm "$MODPATH/$SCRIPT" 0 0 0755
done
