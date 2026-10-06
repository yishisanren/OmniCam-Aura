# OmniCam Aura 1.0.1-x9spro.1

适配目标：Find X9s Pro（PME110），固件 PME110_17.0.0.102(CN01)，相机 7.006.105。
安装器校验机型、固件及原厂相机和算法库 SHA-256；其他组合会拒绝安装。
已在上述真机验证 GR 五种风格及五个焦段、POP 前后摄及实况照片、超清清透滤镜约 5000 万/2 亿像素保存、调色盘交互及 GR 水印编辑后的成片。远距离自动对焦、RAW、长时间拍摄及全部参数组合尚未验收；仅供这组固件使用。

安装此 KernelSU 模块后，安装同版配套 APK `OmniCam-Aura-1.0.1-x9spro.1.apk`，在 LSPosed 中启用并勾选相机 `com.oplus.camera` 和相册 `com.coloros.gallery3d`，然后重启并解锁。Aura 与 Muse 只能启用其一。
需要启用 NoMount metamodule，动态库在固件校验通过后通过 NoMount 注册。APK 没有桌面图标。

移植保留本机 MTK 算法、镜头 ID、原厂模式、ISP 和 gamma。GR 模式提供 15/23/46/65/130mm；46mm 为主摄裁切，130mm 为长焦裁切，新增的 GR/POP 拍摄会话复用本机原厂流程。

卸载前先解锁设备并关闭相机和相册，再从 KernelSU 卸载本模块、从 LSPosed 停用 Aura，重启。
卸载脚本恢复模块改写前的资源目录，不清除照片、应用设置或账号。
若需要先禁用排查，可在解锁后以 root 执行模块目录下的 `restore-resources.sh`，再禁用模块并重启。
OTA 更新后应重新适配；版本校验会停用旧偏移 Hook，不能据此保证旧模块在新系统上可用。

源码、构建说明和授权范围见仓库根目录的 README.md 与 LICENSE。
