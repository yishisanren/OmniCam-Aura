package local.omnicam.aura;
import android.app.Activity;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.IXposedHookZygoteInit;
import de.robv.android.xposed.callbacks.XC_LoadPackage;
import local.jiege.hook.common.Symbols;
import local.jiege.hook.common.Log;
import local.jiege.hook.filters.FilterGroupInjector;
import local.jiege.hook.gr.GrPort;
import local.jiege.hook.highpixel.HighPixelEffects;
import local.jiege.hook.pop.PopPort;
import local.jiege.hook.x10.X10FilterPort;

public final class ModuleEntry implements IXposedHookLoadPackage, IXposedHookZygoteInit {
    @Override public void initZygote(StartupParam param) {
        Symbols.setModulePath(param.modulePath);
        DeviceGuard.load(param.modulePath);
    }
    @Override public void handleLoadPackage(XC_LoadPackage.LoadPackageParam param) {
        if (!DeviceGuard.matchesDevice()) return;
        ClassLoader loader = param.classLoader;
        if ("com.coloros.gallery3d".equals(param.packageName)) {
            Symbols.install("gallery", loader, param.appInfo.sourceDir, param.appInfo.dataDir);
            Log.guard("Aura", "gallery", () -> GrPort.installGallery(loader));
        } else if ("com.oplus.camera".equals(param.packageName)) {
            if (!DeviceGuard.cameraReady(param.appInfo.sourceDir, param.appInfo.dataDir)) {
                Log.i("Aura", "paired resources not active; keeping stock camera behavior");
                return;
            }
            Log.guard("Aura", "native", () -> {
                System.loadLibrary("aura_native");
                Log.i("Aura", "native " + NativeStatus.snapshot());
            });
            XposedBridge.hookAllMethods(Activity.class, "onResume", new XC_MethodHook() {
                private boolean reported;
                @Override protected void afterHookedMethod(MethodHookParam hook) {
                    new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(() ->
                        Log.guard("Aura", "native ready", () -> Log.i("Aura", "native ready " + NativeStatus.snapshot())), 2500);
                    if (reported) return;
                    reported = true;
                    Log.guard("Aura", "runtime evidence", () -> {
                        Class<?> config = XposedHelpers.findClass("com.oplus.camera.configure.CameraConfig", loader);
                        Class<?> unit = XposedHelpers.findClass("com.oplus.ocs.camera.appinterface.adapter.CameraUnitUtils", loader);
                        for (String key : new String[]{"com.oplus.gr.mode.support", "com.oplus.feature.retro.camera.support"}) {
                            Log.i("Aura", key + " app=" + XposedHelpers.callStaticMethod(config, "getConfigBooleanValue", key)
                                + " sdk=" + XposedHelpers.callStaticMethod(unit, "getVendorTagConfig", key));
                        }
                        Log.i("Aura", "native resumed " + NativeStatus.snapshot());
                    });
                }
            });
            Symbols.install("camera", loader, param.appInfo.sourceDir, param.appInfo.dataDir);
            Log.guard("Aura", "POP", () -> PopPort.installCamera(loader, "com.oplus.camera".equals(param.processName)));
            Log.guard("Aura", "filters", () -> FilterGroupInjector.installCamera(loader));
            Log.guard("Aura", "X10", () -> X10FilterPort.installCamera(loader));
            Log.guard("Aura", "high pixel", () -> HighPixelEffects.installCamera(loader));
            Log.guard("Aura", "GR", () -> GrPort.installCamera(loader));
        }
    }
}
