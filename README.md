# OmniCam Aura · Find X9s Pro

为 OPPO Find X9s Pro 移植 GR、POP、清透/琥珀滤镜和调色盘的 KernelSU 模块与 LSPosed 插件。基于 [benbaobaoshigemi/OmniCam-Aura](https://github.com/benbaobaoshigemi/OmniCam-Aura)，以本机 MTK 原厂配置为基础，保留镜头、ISP、gamma 和 AlgoInterface。

**新版：[Release v1.1](https://github.com/yishisanren/OmniCam-Aura/releases/tag/v1.1)** · [详细移植及验收记录](PORTING.md) · [更新记录](CHANGELOG.md)

![OmniCam Aura 图标](artwork/OmniCam-Aura.png)

## 适配范围

| 项目 | 本次验证的组合 |
| --- | --- |
| 机型 | OPPO Find X9s Pro，型号 `PME110` |
| 平台 | MediaTek `MT6993` |
| 系统 | ColorOS 17 / Android 17，固件 `PME110_17.0.0.103(CN01)` |
| 原厂相机 | `7.006.121`，位于 `/product/app/OplusCamera/OplusCamera.apk` |
| Root 环境 | KernelSU，本次实机为 Mountify `2.0.4`；保留 NoMount 路径支持 |
| Hook 环境 | LSPosed；本次实机为 `2.2.1 (7912)` |

这是指定固件的移植版，不是 Find X9 系列通用包。上游 Find X9 Ultra 的 Qualcomm 配置不能直接用于本机。安装器校验机型、固件、原厂相机及算法库；OTA 或相机更新后应重新验证，不能仅凭机型名称继续使用。

## 功能与验证状态

v1.1 已覆盖安装、重启并完成当前固件复测。构建、lint、签名、原厂配置守恒及相机 195 项／相册 20 项接口匹配通过；相机进程实际可见的 14 项配置、库和 LUT 指纹全部匹配，四个 OverlayFS 挂载只读，资源自动初始化完成。

| v1.1 本次实测 | 结果与边界 |
| --- | --- |
| 普通照片 | 保存并完整解码 |
| GR 单色、高对比度黑白 | 均保存并完整解码；成片中心区域通过灰度检查，原生处理和 LUT 加载有运行日志 |
| POP 后摄胶片、CCD | 均保存并完整解码 |
| 超清清透滤镜 | 面板展开、选择及拍照保存通过；本次清透和标准样片均为 3084×4612，未达到界面标称 5000 万像素，原因未定位。5000 万／2 亿像素输出不列为新版通过项 |
| 模式切换后的 4K 录像 | 3840×2160、HEVC＋AAC，约 27.0 秒、平均约 60fps，完整解码通过；测试期间相机进程未重启，未发现该进程崩溃记录 |

以下为 v1.0 在固件 17.0.0.102 / 相机 7.006.105 上的历史实测，未在本次复测的组合不能沿用为 v1.1 通过项。

| 功能 | 实测结果 |
| --- | --- |
| GR 风格 | 标准、单色、高对比度黑白、正片、负片均拍摄保存并解码；两种黑白风格的成片为灰度 |
| GR 焦段 | 15 / 23 / 46 / 65 / 130mm 均保存，EXIF 等效焦距一致；46mm 为主摄裁切，130mm 为长焦裁切 |
| GR Snap | 1m 状态下拍摄保存；其他距离和对焦精度未验收 |
| POP | 后摄胶片、CCD、前摄人脸场景均保存；实况照片的嵌入视频与音频解析正常 |
| 超清滤镜 | 清透滤镜在约 5000 万及 2 亿像素模式下保存，照片完整解码 |
| 调色盘 | 影调、饱和度可调整并拍摄保存；实测参数为 58 / 70 |
| GR 水印 | 可从相机进入相册选择和编辑，应用后成片的底框、标志与机型文本一致 |
| 普通拍摄 | 普通前后摄、人像保存；最终重启后三段 4K 录像保存并完整解码，包含 GR → POP → 超清 → 视频切换后的录像 |

清透/琥珀、柔光和 AI 构图相关资源及配置已包含，但没有完成所有组合和 AI 服务效果的验收。GR 成片有风格差异，不代表已证明与 Ricoh 原厂色彩完全一致。各项证据边界见 [PORTING.md](PORTING.md)。

### 已知问题

- v1.1 超清模式界面标称 5000 万像素，但本次标准和清透样片均输出 3084×4612（含水印边框）。尚未确定是当前设置、原厂流程还是移植影响；不要据此认为已获得完整 5000 万／2 亿像素成片。
- 后期测试曾出现录像提示“录制时间过短”、没有保存文件的现象。重启后三段 4K 录像恢复，时长约 17.4、7.4、22.1 秒；两段长录像平均约 60fps。根因尚未确定，不能承诺长时间运行后不再发生。
- 停用 Aura 的 LSPosed Hook 后也复现过录像异常，但当时配置和库覆盖仍在，这不是完整原厂对照，不能据此排除移植影响。遇到复发应保留日志，再按下方步骤回退排查。
- 远距离自动对焦、RAW、低光画质、长期连续运行和全部滤镜/美颜/柔光组合尚未验收。静物场景的人像照片不能证明虚化质量。
- 原厂调色盘滚动数字控件的无障碍文本可能仍显示 `00`，应看屏幕实际数值。裁切及水印底框会改变最终图片尺寸。

## 安装

在 [v1.1 发行页](https://github.com/yishisanren/OmniCam-Aura/releases/tag/v1.1) 下载同一发行版的两个安装包：

- `OmniCam-Aura-1.1.0-x9spro.1-KSU.zip`：KernelSU 模块。
- `OmniCam-Aura-1.1.0-x9spro.1.apk`：LSPosed 插件。

1. 确认上表的固件与相机版本，并启用 Mountify 或 NoMount metamodule。停用其他 OmniCam Aura / Muse 模块，避免相机 Hook 和资源重叠。
2. 在 KernelSU / SukiSU 中安装 ZIP。
3. 安装 APK，在 LSPosed 启用 `local.omnicam.aura`，只勾选相机 `com.oplus.camera` 和相册 `com.coloros.gallery3d`。
4. 重启并解锁，等待模块资源初始化，再打开原厂相机。可在模式栏选择 POP 和理光 GR。

APK 没有桌面图标和独立设置入口，功能通过原厂相机及相册使用。若安装器拒绝当前固件，不要删掉校验强行安装。

`v1.1` 的内部构建版本为 `1.1.0-x9spro.1`。固件 17.0.0.102 / 相机 7.006.105 仍对应旧 [v1.0](https://github.com/yishisanren/OmniCam-Aura/releases/tag/v1.0)，请按固件选择配套 APK/ZIP。下载后可用发行页的 `SHA256SUMS.txt` 校验文件。

APK 在配套资源未完整加载、配置或库指纹不符时保持原厂相机行为；只安装 APK 或尚未重启不会启用移植拍摄链路。

## 回退与卸载

首次解锁初始化时，模块会备份它要覆盖的资源目录到 `/data/adb/omnicam_aura_x9spro_backup`，更新时保留备份。模块通过文件挂载及受校验的库覆盖加载资源，不直接改写系统分区。

正常卸载：先解锁，关闭相机和相册，从 KernelSU / SukiSU 卸载 `omnicam_aura_x9spro`，在 LSPosed 停用 Aura，然后重启。恢复脚本只处理模块覆盖的资源，不删除照片或账号。

如果需要先禁用模块排查，应在解锁、关闭相机和相册后先以 root 执行：

```sh
su -c 'sh /data/adb/modules/omnicam_aura_x9spro/restore-resources.sh'
```

脚本成功后再禁用本模块、停用 Aura 并重启。恢复脚本已通过语法和路径检查，尚未做真机完整卸载演练。

## 从源码构建

本分支的构建入口是 `tools/build_x9spro.sh`，已在 macOS 验证。上游 `build.ps1` 和 `tools/verify_aura.py` 面向原始 PMA110 发行版，不用于本移植版。

需要 JDK 21、Python 3、Android SDK API 37、Build Tools 36、NDK `29.0.14206865`、CMake `3.22.1`。设置 `JAVA_HOME` 和 `ANDROID_HOME` 后运行：

```sh
sh tools/build_x9spro.sh
```

产物输出到 `dist/`，构建目录默认位于本机缓存，避免云同步目录生成文件冲突。脚本执行 assemble、lint、签名及包结构校验；存在私有原厂快照时还会执行配置守恒校验。没有快照时只验证安装包结构与资源一致性，不能替代真机验收。

默认使用 Android 调试签名。自行构建通常会使用不同的本地调试证书，不能直接覆盖发行版 APK。使用自己的证书时可设置 `OMNICAM_KEYSTORE`、`OMNICAM_STORE_PASSWORD`、`OMNICAM_KEY_ALIAS`、`OMNICAM_KEY_PASSWORD`；不要提交证书和密码。

`tools/prepare_x9spro.py` 用于从原厂快照重新生成配置（用 `AURA_STOCK_DIR` 指向当前固件快照，目录内 `device-profile.json` 记录 model、firmware、camera 和 camera_apk），`tools/verify_x9spro.py` 用于配置与包校验。原厂快照、真机媒体、账号数据、运行日志、签名密钥及本机工具缓存不会提交到 Git。真机辅助脚本通过 `AURA_DEVICE_SERIAL` 指定设备，读回检查还依赖安装前的私有快照。

## 来源与许可

- 上游：[benbaobaoshigemi/OmniCam-Aura](https://github.com/benbaobaoshigemi/OmniCam-Aura)。本仓库是其 Find X9s Pro 移植分支，保留上游历史和归属。
- 四个补齐的 GR LUT 来自 [TheMuppets 的 OnePlus dodge 厂商资源](https://github.com/TheMuppets/proprietary_vendor_oneplus_dodge/tree/5cdea50164c2c9435e8612da132396877acd8730/proprietary/odm/etc/camera/meishe_lut)，固定 commit、Git blob、长度与 SHA-256 记录在 [gr-lut-sources.json](module/payload/gr-lut-sources.json)。
- 原创源码和脚本按 [MIT](LICENSE) 开放。厂商库、固件配置、媒体、字体及第三方依赖保留原权利人的授权条件，MIT 不授予这些文件的再许可。项目与 OPPO、Ricoh 或其他相机厂商无隶属关系。
