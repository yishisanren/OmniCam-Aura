#!/system/bin/sh
set -eu
MODDIR=${0%/*}
NOMOUNT=/data/adb/modules/nomount/bin/nm
exec >> "$MODDIR/libraries.log" 2>&1
[ "$(getprop ro.product.model)" = PME110 ] || exit 0
[ "$(getprop ro.build.display.id)" = 'PME110_17.0.0.102(CN01)' ] || exit 0
[ "$(sha256sum /odm/lib64/libAlgoInterface.so | cut -d ' ' -f 1)" = 8e6ce18cefae51089b8318970daea3087fb6434fed42d55810bf7456df8d66e5 ] || exit 0
"$NOMOUNT" version

bind_library() {
    NAME=$1
    SOURCE="$MODDIR/system/odm/lib64/$NAME"
    TARGET="/odm/lib64/$NAME"
    test -f "$SOURCE"
    chown root:root "$SOURCE"
    chmod 0644 "$SOURCE"
    chcon u:object_r:same_process_hal_file:s0 "$SOURCE"
    "$NOMOUNT" rule add "$TARGET" "$SOURCE"
    echo "redirect ok $TARGET"
}

# skip_mount prevents automatic library overlays before firmware validation.
bind_library libBasicTonePhotoX9.so
bind_library libBasicTonePhotoX10.so
bind_library libBasicTonePhoto.so
bind_library libmsnativefilter.so
