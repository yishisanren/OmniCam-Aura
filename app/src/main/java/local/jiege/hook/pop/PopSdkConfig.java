package local.jiege.hook.pop;

import de.robv.android.xposed.XposedHelpers;
import local.jiege.hook.common.SuperCall;

/** Use this firmware's photo session selection, including MTK's no-YUV Turbo HDR case. */
final class PopSdkConfig {
    private PopSdkConfig() {}

    static void install(ClassLoader classLoader) throws Throwable {
        Class<?> retro = XposedHelpers.findClass("com.oplus.ocs.camera.producer.mode.RetroCameraMode", classLoader);
        Class<?> photo = XposedHelpers.findClass("com.oplus.ocs.camera.producer.mode.PhotoMode", classLoader);
        SuperCall.inherit(retro, photo, "getSurfaceUseCase", String.class, Boolean.TYPE, Float.class);
    }
}
