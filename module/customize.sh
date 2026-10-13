#!/system/bin/sh
# Installation is limited to the firmware actually inspected for this port.
. "$MODPATH/device-profile.sh"
aura_device_matches || abort "Device firmware, active camera or original MTK library differs from this package's inspected profile."
[ "$(pm path com.oplus.camera)" = 'package:/product/app/OplusCamera/OplusCamera.apk' ] || abort "The active camera is an uninspected update."
if [ -x /data/adb/modules/nomount/bin/nm ] && [ ! -e /data/adb/modules/nomount/disable ]; then
    ui_print "NoMount library redirects available."
elif [ -f /data/adb/modules/mountify/metamount.sh ] && [ ! -e /data/adb/modules/mountify/disable ]; then
    ui_print "Mountify environment: guarded read-only camera library overlay."
else
    abort "An active NoMount or Mountify metamodule is required."
fi
for OTHER in /data/adb/modules/omnicam_aura /data/adb/modules/omnicam_muse; do
    if [ -d "$OTHER" ] && [ ! -e "$OTHER/disable" ] && [ ! -e "$OTHER/remove" ]; then
        abort "Disable the other OmniCam module first."
    fi
done
ui_print "PME110 / original MTK libraries verified."
set_perm_recursive "$MODPATH" 0 0 0755 0644
for SCRIPT in customize.sh device-profile.sh post-fs-data.sh post-mount.sh service.sh uninstall.sh restore-resources.sh; do
    set_perm "$MODPATH/$SCRIPT" 0 0 0755
done
