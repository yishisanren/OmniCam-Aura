#pragma once
#include <cstddef>
using HookFunction = int (*)(void *, void *, void **);
void hookExport(HookFunction, void *, const char *, void *, void **, const char *);
void installPopPathRemap(HookFunction);
void onLibraryLoadedForGr(HookFunction, const char *, void *);
void activateLoadedLibrariesForGr(HookFunction);
unsigned grNativeHookStatus();
unsigned grNativeFrameCount();
unsigned grNativeLutCount();
