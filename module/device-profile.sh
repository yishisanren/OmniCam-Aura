#!/system/bin/sh
AURA_MODEL='PME110'
AURA_FIRMWARE='PME110_17.0.0.103(CN01)'
AURA_CAMERA_SHA256='6ff0a021288529bdd8eb957827322c71b85c50c93b1715f9e34ab77a7c70a0e6'
AURA_ALGO_SHA256='8e6ce18cefae51089b8318970daea3087fb6434fed42d55810bf7456df8d66e5'
aura_device_matches() {
    [ "$(getprop ro.product.model)" = "$AURA_MODEL" ] &&
    [ "$(getprop ro.build.display.id)" = "$AURA_FIRMWARE" ] &&
    [ "$(sha256sum /product/app/OplusCamera/OplusCamera.apk | cut -d " " -f 1)" = "$AURA_CAMERA_SHA256" ] &&
    [ "$(sha256sum /odm/lib64/libAlgoInterface.so | cut -d " " -f 1)" = "$AURA_ALGO_SHA256" ]
}
aura_mounts_match() {
    [ "$(sha256sum /odm/etc/camera/config/camera_unit_config | cut -d " " -f 1)" = "20d7d57e8651af9949a92f3e4214996fe84887d20a32bffe44c4d06738ceb5cb" ] || return 1
    [ "$(sha256sum /odm/etc/camera/config/camera_unit_feature_config.protobuf | cut -d " " -f 1)" = "4dfdcc5e40724ac857440bc17da5905fcce42ad4f98da0054f3fa4be5d907e14" ] || return 1
    [ "$(sha256sum /odm/etc/camera/config/oplus_camera_config | cut -d " " -f 1)" = "fe7aec972c033541b7e78692f0a6c213cf1d5ff396a2f501c820852c854c9627" ] || return 1
    [ "$(sha256sum /odm/etc/camera/config/oplus_camera_algo_switch_config | cut -d " " -f 1)" = "f4acfc46a339a222481499dd53770dc298d517e7d7792d18465a29481687011d" ] || return 1
    [ "$(sha256sum /odm/etc/camera/config/oplus_camera_aps_config | cut -d " " -f 1)" = "d5bb514648cc426beac92a0864c07bacb0d0a58546ee01a4c31a3e38007e4731" ] || return 1
    [ "$(sha256sum /odm/lib64/libBasicTonePhoto.so | cut -d " " -f 1)" = "3aaa79dc15bde658d718cb5e8b60c566e9221b038b2cc60fbe160dfd1a58fe09" ] || return 1
    [ "$(sha256sum /odm/lib64/libBasicTonePhotoX10.so | cut -d " " -f 1)" = "56ef69910177f1766d2ca922da0c1aa3ef1893ecc9b3892cff986bfc112a95cc" ] || return 1
    [ "$(sha256sum /odm/lib64/libBasicTonePhotoX9.so | cut -d " " -f 1)" = "57941d57cb81bebb5eb52bf5779bdee7e2932ea038efb590cbe1c8837457ebbe" ] || return 1
    [ "$(sha256sum /odm/lib64/libmsnativefilter.so | cut -d " " -f 1)" = "e0a97aaf700515c1f4d5e3cb3944a154cd979860d811d65c03930f1a261e0b36" ] || return 1
    [ "$(sha256sum /odm/lib64/libAlgoInterface.so | cut -d " " -f 1)" = "8e6ce18cefae51089b8318970daea3087fb6434fed42d55810bf7456df8d66e5" ] || return 1
    [ "$(sha256sum /odm/etc/camera/meishe_lut/gr.bw.rgba.bin | cut -d " " -f 1)" = "983ac9d5a691182fa6685de85bacd2177110b304f388fe691d5b3ddaef47e1b5" ] || return 1
    [ "$(sha256sum /odm/etc/camera/meishe_lut/gr.hi.bw.rgba.bin | cut -d " " -f 1)" = "b14d5f583784d1af7089b69611f4ae8e1cf2b016fcec0efd7b899c85dcf1007c" ] || return 1
    [ "$(sha256sum /odm/etc/camera/meishe_lut/gr.nega.rgba.bin | cut -d " " -f 1)" = "d176b014cac5f642e4ead0af8d79fe23b0354e6a3d213f444d5e6f6e1e4ae095" ] || return 1
    [ "$(sha256sum /odm/etc/camera/meishe_lut/gr.posi.rgba.bin | cut -d " " -f 1)" = "ca265ce4df8109647274757412e98831f89b1d90975130e00fa07d3c763ab84c" ] || return 1
    return 0
}
