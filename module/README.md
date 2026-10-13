# OmniCam Aura 1.1.0-x9spro.1

适配目标：Find X9s Pro（PME110），固件 PME110_17.0.0.103(CN01)，相机 7.006.121。
安装器校验机型、固件及原厂相机和算法库 SHA-256；其他组合会拒绝安装。
当前固件已验证安装、重启初始化、相机进程挂载，以及普通照片、GR 两种黑白风格、POP 胶片/CCD 和约 27 秒 4K 60fps 录像保存与完整解码。超清清透的最终成片为 6144×9184（含水印边框）并完整解码。2 亿像素、远距离自动对焦、RAW、长时间拍摄及全部参数组合本次尚未验收；仅供这组固件使用。

安装此 KernelSU 模块后，安装同版配套 APK `OmniCam-Aura-1.1.0-x9spro.1.apk`，在 LSPosed 中启用并勾选相机 `com.oplus.camera` 和相册 `com.coloros.gallery3d`，然后重启并解锁。Aura 与 Muse 只能启用其一。
需要启用 Mountify 或 NoMount metamodule。Mountify 环境通过设备校验后，为配置、资源和库建立四个只读 OverlayFS；NoMount 环境保留原有 bind mount 与库路径规则。APK 没有桌面图标。

移植保留本机 MTK 算法、镜头 ID、原厂模式、ISP 和 gamma。GR 模式提供 15/23/46/65/130mm；46mm 为主摄裁切，130mm 为长焦裁切，新增的 GR/POP 拍摄会话复用本机原厂流程。

卸载前先解锁设备并关闭相机和相册，再从 KernelSU 卸载本模块、从 LSPosed 停用 Aura，重启。
卸载脚本恢复模块改写前的资源目录，不清除照片、应用设置或账号。
若需要先禁用排查，可在解锁后以 root 执行模块目录下的 `restore-resources.sh`，再禁用模块并重启。
OTA 更新后应重新适配；版本校验会停用旧偏移 Hook，不能据此保证旧模块在新系统上可用。

源码、构建说明和授权范围见仓库根目录的 README.md 与 LICENSE。
