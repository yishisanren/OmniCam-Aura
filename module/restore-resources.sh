#!/system/bin/sh
set -eu
MODDIR=${0%/*}
BACKUPDIR=/data/adb/omnicam_aura_x9spro_backup
[ -f "$BACKUPDIR/ready" ] || exit 0
if [ "$(getprop sys.user.0.ce_available)" != true ]; then
    echo "Unlock the phone before restoring camera resources." >&2
    exit 1
fi
for TARGET in /data/user/0/com.oplus.camera/files/ricoh_gr /data/user/0/com.oplus.camera/files/pop_port /data/user/0/com.oplus.camera/files/jiege/fonts /data/user/0/com.oplus.camera/files/mode_limit_watermark /data/user/0/com.oplus.camera/files/odm/etc/camera/pld_watermark /data/user/0/com.coloros.gallery3d/files/ricoh_gr_styles; do
    BACKUP="$BACKUPDIR/resources/${TARGET#/}"
    rm -rf "$TARGET"
    if [ -e "$BACKUP" ]; then
        mkdir -p "${TARGET%/*}"
        cp -a "$BACKUP" "$TARGET"
        restorecon -R "$TARGET"
    fi
done
echo "Original camera resources restored. Photos, settings and accounts preserved."
