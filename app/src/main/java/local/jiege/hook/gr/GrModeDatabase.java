package local.jiege.hook.gr;

import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import java.util.List;
import local.jiege.hook.common.Log;
import local.jiege.hook.common.Symbols;

/** Reconcile supported modes when the camera APK version itself has not changed. */
final class GrModeDatabase {
    private GrModeDatabase() {}

    static void install(Symbols symbols) {
        XposedBridge.hookMethod(symbols.method("ModeDb.initialize"), new XC_MethodHook() {
            @Override protected void afterHookedMethod(MethodHookParam param) {
                if (param.hasThrowable()) return;
                Log.guard("Aura", "mode registration", () -> {
                    Object db = param.thisObject;
                    List<?> headline = (List<?>) symbols.call("ModeDb.query", db, "position_headline", false, false);
                    List<?> panel = (List<?>) symbols.call("ModeDb.query", db, "position_mode_panel", false, false);
                    // The stock reconciler checks both lists, inserts only missing supported modes,
                    // and preserves the user's existing positions and ranks.
                    symbols.call("ModeDb.addHeadline", db, null, headline, panel);
                    symbols.call("ModeDb.addPanel", db, null, headline, panel);
                    List<?> after = (List<?>) symbols.call("ModeDb.query", db, "position_headline", false, false);
                    Log.i("Aura", "mode registration headline=" + headline.size() + " -> " + after.size());
                });
            }
        });
    }
}
