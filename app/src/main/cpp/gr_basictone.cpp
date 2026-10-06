// GR port, native half.
//
// The GR mode reuses the professional (master) capture pipeline. GR frames are recognised by the
// gr_effect_size APS setting (63) and get:
//   * BasicTone: the GR LMT/SC/CWCM tree (staged by service.sh) instead of the host ODM tree;
//   * no artistic vignette from the V1 vignette parameters;
//   * the Meishe V1 filter node (clarity, vignette, grain), run with the GR capture mode.
// Offsets are verified against PME110_17.0.0.102 / Camera 7.006.105.
#include <android/log.h>
#include <cstdint>
#include <cstring>
#include <dlfcn.h>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>
#include <atomic>
#include <fstream>

#include "native_hooks.h"
#include "firmware_guard.h"

namespace {

constexpr char kTag[] = "RicohGrPort";
constexpr char kGrLmtPath[] = "/data/user/0/com.oplus.camera/files/ricoh_gr/lmt";
constexpr char kHostLmtPath[] = "/odm/etc/camera/basictone/lmt";
constexpr uint32_t kGrCaptureMode = 37;

// APS setting keys use libc++'s 24-byte short-string layout on this firmware.
struct alignas(8) SettingKey {
    uint8_t length;
    char text[23];
};
const SettingKey kGrSizeKey = {28, "gr_effect_size"};

int (*getSettingInt)(void *settings, const void *key, int fallback);
void (*originalGetLmtParams)(void *, void *, int);
void (*originalGetVigParams)(void *, void *, void *);
int (*originalFilterProcessV2)(void *, int);
int (*filterProcessV1)(void *, int);
int (*filterRegisterV1)(void *, int);
int (*filterUnregisterV1)(void *, int);
uintptr_t (*originalProcessCore)(void *, void *, void *, void *, void *);
uintptr_t (*originalLoadLut)(void *, int);
std::mutex hookMutex;
std::atomic<unsigned> installedHooks{};
std::atomic<unsigned> grFrames{};
std::atomic<unsigned> grLutLoads{};

// getLmtParamsV1 runs per frame before BasicTone; remember which LUT tree belongs to each parameter
// block so processCore/loadLut (which no longer see the frame) can pick it.
enum Profile { kUnknown = -1, kHost = 0, kGr = 1 };
struct FrameProfile {
    Profile profile = kHost;
};
std::mutex profileMutex;
std::unordered_map<void *, FrameProfile> frameProfiles;
thread_local int activeProfile = kUnknown;

bool isGrFrame(void *frame) {
    if (!frame || !getSettingInt) return false;
    void *settings = *reinterpret_cast<void **>(static_cast<char *>(frame) + 0x8110);
    return settings && getSettingInt(settings, &kGrSizeKey, 0) == 63;
}

void getLmtParams(void *parameters, void *frame, int stage) {
    bool gr = isGrFrame(frame);
    if (gr) ++grFrames;
    originalGetLmtParams(parameters, frame, stage);
    FrameProfile profile;
    profile.profile = gr ? kGr : kHost;
    std::lock_guard<std::mutex> lock(profileMutex);
    frameProfiles[parameters] = profile;
}

void getVigParams(void *parameters, void *frame, void *planes) {
    originalGetVigParams(parameters, frame, planes);
    if (isGrFrame(frame)) static_cast<uint8_t *>(parameters)[0x1a] = 0;
}

int withGrCaptureMode(int (*operation)(void *, int), void *frame, int stage) {
    auto *mode = reinterpret_cast<uint32_t *>(static_cast<char *>(frame) + 0x18);
    uint32_t previous = *mode;
    *mode = kGrCaptureMode;
    int result = operation(frame, stage);
    *mode = previous;
    return result;
}

int filterProcessV2(void *frame, int stage) {
    if (!isGrFrame(frame)) return originalFilterProcessV2(frame, stage);
    // Registration happens before gr_effect_size is attached, so the V1 node's whole lifecycle
    // is scoped to this call, where the frame is known to be GR. The per-image object is
    // consumed after capture; session and request modes are untouched.
    int registration = withGrCaptureMode(filterRegisterV1, frame, stage);
    if (registration != 0) return registration;
    int result = withGrCaptureMode(filterProcessV1, frame, stage);
    withGrCaptureMode(filterUnregisterV1, frame, stage);
    return result;
}

uintptr_t processCore(void *object, void *input, void *output, void *parameters, void *metadata) {
    int previous = activeProfile;
    activeProfile = kUnknown;
    FrameProfile profile;
    bool known = false;
    {
        std::lock_guard<std::mutex> lock(profileMutex);
        auto found = frameProfiles.find(parameters);
        if (found != frameProfiles.end()) {
            profile = found->second;
            known = true;
            frameProfiles.erase(found);
        }
    }
    if (known) {
        activeProfile = profile.profile;
    }
    uintptr_t result = originalProcessCore(object, input, output, parameters, metadata);
    activeProfile = previous;
    return result;
}

uintptr_t loadLut(void *object, int mode) {
    // Intermediate ODT passes carry no profile; they keep the object's current LUTs.
    if (activeProfile != kUnknown) {
        char *lmtPath = static_cast<char *>(object) + 0x008;  // 256-byte path buffer
        const char *desired = activeProfile == kGr ? kGrLmtPath : kHostLmtPath;
        if (std::strlen(desired) < 240 && std::strcmp(lmtPath, desired) != 0) {
            std::strcpy(lmtPath, desired);
            // The path is not part of the vendor cache key, so a profile switch forces a reload.
            *reinterpret_cast<int *>(static_cast<char *>(object) + 0xeb0) = -1;
            if (activeProfile == kGr) ++grLutLoads;
            __android_log_print(ANDROID_LOG_INFO, kTag, "BasicTone profile=%s path=%s",
                                activeProfile == kGr ? "GR" : "host", desired);
        }
    }
    return originalLoadLut(object, mode);
}

bool installGrAddress(HookFunction hook, void *address, void *replacement, void **backup, unsigned flag) {
    if (!hook || !address || hook(address, replacement, backup) != 0) return false;
    installedHooks.fetch_or(flag);
    return true;
}

void hookAlgoBase(HookFunction hook, void *base) {
    std::lock_guard<std::mutex> lock(hookMutex);
    if (!hasBuildId(base, "d8bd771877bb9f58cb6ee198b68af51a")) return;
    auto at = [base](uintptr_t offset) { return static_cast<char *>(base) + offset; };
    // Addresses are exported-symbol values read from this exact original MTK ELF.
    getSettingInt = reinterpret_cast<decltype(getSettingInt)>(at(0xa252d0));
    filterProcessV1 = reinterpret_cast<decltype(filterProcessV1)>(at(0xff1000));
    filterRegisterV1 = reinterpret_cast<decltype(filterRegisterV1)>(at(0xfee710));
    filterUnregisterV1 = reinterpret_cast<decltype(filterUnregisterV1)>(at(0xfef6b0));
    if (!originalGetLmtParams) installGrAddress(hook, at(0x1598bc0), reinterpret_cast<void *>(getLmtParams),
        reinterpret_cast<void **>(&originalGetLmtParams), 1);
    if (!originalFilterProcessV2) installGrAddress(hook, at(0x1006bc0), reinterpret_cast<void *>(filterProcessV2),
        reinterpret_cast<void **>(&originalFilterProcessV2), 2);
    if (!originalGetVigParams) installGrAddress(hook, at(0x1597520), reinterpret_cast<void *>(getVigParams),
        reinterpret_cast<void **>(&originalGetVigParams), 4);
}

void hookBasicToneBase(HookFunction hook, void *base) {
    std::lock_guard<std::mutex> lock(hookMutex);
    if (!hasBuildId(base, "b125b367260781e1eee0aeec834b3dc91501a3aa")) return;
    auto at = [base](uintptr_t offset) { return static_cast<char *>(base) + offset; };
    if (!originalProcessCore) installGrAddress(hook, at(0x53b90), reinterpret_cast<void *>(processCore),
        reinterpret_cast<void **>(&originalProcessCore), 8);
    if (!originalLoadLut) installGrAddress(hook, at(0x51934), reinterpret_cast<void *>(loadLut),
        reinterpret_cast<void **>(&originalLoadLut), 16);
}

}  // namespace

void activateLoadedLibrariesForGr(HookFunction hook) {
    struct Library { std::string name; void *base; };
    std::vector<Library> libraries;
    // Android namespaces hide SDK libraries from the module's dl_iterate_phdr.
    // Only existing readable ELF mappings are considered, then their GNU Build IDs are checked.
    std::ifstream maps("/proc/self/maps");
    std::string line;
    while (std::getline(maps, line)) {
        if (line.find("libAlgoInterface.so") == std::string::npos
            && line.find("libBasicTonePhoto") == std::string::npos) continue;
        unsigned long start, end, offset;
        char permissions[5]{};
        if (std::sscanf(line.c_str(), "%lx-%lx %4s %lx", &start, &end, permissions, &offset) != 4
            || offset != 0 || permissions[0] != 'r') continue;
        libraries.push_back({line, reinterpret_cast<void *>(start)});
    }
    for (const auto &library : libraries) {
        if (library.name.find("libAlgoInterface.so") != std::string::npos) hookAlgoBase(hook, library.base);
        else hookBasicToneBase(hook, library.base);
    }
}

unsigned grNativeHookStatus() { return installedHooks.load(); }
unsigned grNativeFrameCount() { return grFrames.load(); }
unsigned grNativeLutCount() { return grLutLoads.load(); }

void onLibraryLoadedForGr(HookFunction hook, const char *name, void *handle) {
    const char *symbol = nullptr;
    if (std::strstr(name, "libAlgoInterface.so")) {
        symbol = "_ZN7android14getLmtParamsV1ER12ProcessParamPNS_15AlgoProcessDataEi";
    } else if (std::strstr(name, "libBasicTonePhoto")) {
        symbol = "_ZN13BasicTone_OGL11processCoreEP5ImageS1_PvS2_";
    }
    Dl_info info{};
    void *address = symbol ? dlsym(handle, symbol) : nullptr;
    if (address && dladdr(address, &info)) {
        if (std::strstr(name, "libAlgoInterface.so")) hookAlgoBase(hook, info.dli_fbase);
        else hookBasicToneBase(hook, info.dli_fbase);
    }
}
