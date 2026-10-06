// LSPosed native module entry for the camera process (listed in assets/native_init).
#include <android/log.h>
#include <cstdint>
#include <dlfcn.h>
#include <cstring>
#include <sys/system_properties.h>
#include <jni.h>
#include <cstdio>
#include <atomic>

#include "native_hooks.h"

namespace {

struct NativeApiEntries {
    uint32_t version;
    HookFunction hook;
    int (*unhook)(void *);
};

using LibraryLoadedCallback = void (*)(const char *name, void *handle);

HookFunction installHook;
std::atomic<int> activationState{};
std::atomic<int> algoLoads{};
std::atomic<int> basicToneLoads{};

void onLibraryLoaded(const char *name, void *handle) {
    if (std::strstr(name, "libAlgoInterface.so")) ++algoLoads;
    if (std::strstr(name, "libBasicTonePhoto")) ++basicToneLoads;
    onLibraryLoadedForGr(installHook, name, handle);
}


}  // namespace

void hookExport(HookFunction hook, void *handle, const char *symbol, void *replacement,
                void **backup, const char *tag) {
    void *address = dlsym(handle, symbol);
    if (!address || !hook || hook(address, replacement, backup) != 0) {
        __android_log_print(ANDROID_LOG_ERROR, tag, "native hook failed: %s", symbol);
    }
}

extern "C" __attribute__((visibility("default"), used))
LibraryLoadedCallback native_init(const NativeApiEntries *entries) {
    activationState = 1;
    char model[PROP_VALUE_MAX]{}, firmware[PROP_VALUE_MAX]{};
    __system_property_get("ro.product.model", model);
    __system_property_get("ro.build.display.id", firmware);
    if (std::strcmp(model, "PME110") || std::strcmp(firmware, "PME110_17.0.0.102(CN01)")) { activationState = -1; return nullptr; }
    if (!entries || !entries->hook) { activationState = -2; return nullptr; }
    installHook = entries->hook;
    installPopPathRemap(installHook);
    activationState = 2;
    return onLibraryLoaded;
}

extern "C" __attribute__((visibility("default"), used))
jstring Java_local_omnicam_aura_NativeStatus_snapshot(JNIEnv *env, jclass) {
    if (installHook) activateLoadedLibrariesForGr(installHook);
    char status[192];
    std::snprintf(status, sizeof(status), "init=%d algoLoads=%d basicToneLoads=%d hooks=%u grFrames=%u grLutLoads=%u", activationState.load(), algoLoads.load(), basicToneLoads.load(), grNativeHookStatus(), grNativeFrameCount(), grNativeLutCount());
    return env->NewStringUTF(status);
}
