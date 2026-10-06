#!/system/bin/sh
MODDIR=${0%/*}
if sh "$MODDIR/restore-resources.sh"; then
    rm -rf /data/adb/omnicam_aura_x9spro_backup
fi
