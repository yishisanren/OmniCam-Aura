#!/system/bin/sh

MODDIR=${0%/*}
APP=/data/user/0/com.oplus.camera
OUT=$APP/files/ricoh_gr/lmt
BACKUPDIR=/data/adb/omnicam_aura_x9spro_backup

[ "$(getprop ro.product.model)" = PME110 ] || exit 0
[ "$(getprop ro.build.display.id)" = 'PME110_17.0.0.102(CN01)' ] || exit 0
exec >> "$MODDIR/stage.log" 2>&1

until [ "$(getprop sys.boot_completed)" = 1 ] && [ "$(getprop sys.user.0.ce_available)" = true ] && [ -d "$APP" ]; do
    sleep 1
done

APP_UID=$(stat -c %u "$APP")
# Back up only the exact resource paths the module will create or overwrite.
if [ ! -f "$BACKUPDIR/ready" ]; then
    mkdir -p "$BACKUPDIR" || exit 1
    chmod 0700 "$BACKUPDIR"
    rm -rf "$BACKUPDIR/resources"
    for TARGET in "$APP/files/ricoh_gr" "$APP/files/pop_port" "$APP/files/jiege/fonts" "$APP/files/mode_limit_watermark" "$APP/files/odm/etc/camera/pld_watermark" /data/user/0/com.coloros.gallery3d/files/ricoh_gr_styles; do
        REL=${TARGET#/}
        if [ -e "$TARGET" ]; then
            mkdir -p "$BACKUPDIR/resources/${REL%/*}" || exit 1
            cp -a "$TARGET" "$BACKUPDIR/resources/$REL" || exit 1
        fi
    done
    touch "$BACKUPDIR/ready" || exit 1
fi

mkdir -p "$OUT"
for ORIGINAL in /odm/etc/camera/basictone/lmt/*; do
    NAME=${ORIGINAL##*/}
    case "$NAME" in
        SC16*|SC32*|CWCM*)
            cp "$MODDIR/payload/gr_adjustment_lmt/$NAME" "$OUT/$NAME"
            ;;
        *)
            if [ -L "$OUT/$NAME" ]; then rm "$OUT/$NAME"; fi
            if [ -d "$ORIGINAL" ]; then
                mkdir -p "$OUT/$NAME"
                cp -R "$ORIGINAL/." "$OUT/$NAME/"
            else
                cp "$ORIGINAL" "$OUT/$NAME"
            fi
            ;;
    esac
done
chown -R "$APP_UID:$APP_UID" "$APP/files/ricoh_gr"
restorecon -R "$APP/files/ricoh_gr"

# GR watermark fonts: the styles name their fonts by URL, which the camera cannot load. Fonts the
# gallery already downloaded for its watermark editor are copied where the GR hook finds them
# (FZLTZCHK is also in the camera's own files/video_watermark).
GALLERY_FONTS=/data/user/0/com.coloros.gallery3d/files/watermark_master/materia
mkdir -p "$APP/files/jiege/fonts"
for FONT in GilroySemiBold.otf FZLTZCHK.TTF; do
    SOURCE="$GALLERY_FONTS/$FONT"
    [ -f "$SOURCE" ] || SOURCE="$APP/files/video_watermark/$FONT"
    if [ -f "$SOURCE" ]; then
        cp -f "$SOURCE" "$APP/files/jiege/fonts/$FONT"
    fi
done
chown -R "$APP_UID:$APP_UID" "$APP/files/jiege/fonts"
restorecon -R "$APP/files/jiege/fonts"

# Stage POP before the gallery wait so camera resources are ready at startup.
ASSET_DIR="$APP/files/pop_port"
PLD_APP="$APP/files/odm/etc/camera/pld_watermark"
mkdir -p "$ASSET_DIR/setting_Retro" "$ASSET_DIR/meishe_lut" "$ASSET_DIR/pld_watermark" "$ASSET_DIR/apk_resources/json" "$ASSET_DIR/apk_resources/img" "$PLD_APP"
cp -f "$MODDIR/payload/setting_Retro/"* "$ASSET_DIR/setting_Retro/"
cp -f "$MODDIR/payload/meishe_lut/"* "$ASSET_DIR/meishe_lut/"
cp -a "$MODDIR/payload/pld_watermark/." "$ASSET_DIR/pld_watermark/"
cp -a "$MODDIR/payload/pld_watermark/." "$PLD_APP/"
cp -a "$MODDIR/payload/apk_resources/." "$ASSET_DIR/apk_resources/"
chown -R "$APP_UID:$APP_UID" "$APP/files/pop_port" "$PLD_APP"
find "$ASSET_DIR" "$PLD_APP" -type d -exec chmod 0755 {} \;
find "$ASSET_DIR" "$PLD_APP" -type f -exec chmod 0644 {} \;
restorecon -R "$ASSET_DIR" "$PLD_APP" 2>/dev/null || true

GALLERY=/data/user/0/com.coloros.gallery3d
until [ -d "$GALLERY" ]; do
    sleep 1
done
GALLERY_UID=$(stat -c %u "$GALLERY")
STYLE_OUT="$GALLERY/files/ricoh_gr_styles"
mkdir -p "$STYLE_OUT"
cp "$MODDIR/payload/watermark_master_styles/"*.json "$STYLE_OUT/"
if [ -d "$MODDIR/payload/watermark_drawables" ]; then
    cp "$MODDIR/payload/watermark_drawables/"*.webp "$STYLE_OUT/" 2>/dev/null || true
fi
CAM_ML="$APP/files/mode_limit_watermark"
mkdir -p "$CAM_ML"
for i in 1 2 3 4 5; do
    ID="gr_style_${i}"
    NAME="gr_style_${i}.json"
    JSON="$MODDIR/payload/watermark_master_styles/$NAME"
    if [ -f "$JSON" ]; then
        mkdir -p "$CAM_ML/$ID"
        cp -f "$JSON" "$CAM_ML/$ID/$NAME"
        cp -f "$JSON" "$CAM_ML/$NAME"
        if [ -d "$MODDIR/payload/watermark_drawables" ]; then
            cp -f "$MODDIR/payload/watermark_drawables/"*.webp "$CAM_ML/$ID/" 2>/dev/null || true
        fi
    fi
done
if [ -d "$MODDIR/payload/watermark_drawables" ]; then
    cp -f "$MODDIR/payload/watermark_drawables/"*.webp "$CAM_ML/" 2>/dev/null || true
fi
chown -R "$GALLERY_UID:$GALLERY_UID" "$STYLE_OUT"
chmod 0644 "$STYLE_OUT"/*
restorecon -R "$STYLE_OUT"
chown -R "$APP_UID:$APP_UID" "$CAM_ML"
find "$CAM_ML" -type f -exec chmod 0644 {} \;
find "$CAM_ML" -type d -exec chmod 0755 {} \;
restorecon -R "$CAM_ML"
echo "Resource staging complete"
