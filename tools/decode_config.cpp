#include <cstdio>
#include <cstdlib>
#include <dlfcn.h>
#include <fstream>
#include <iterator>
#include <vector>

// Matches OplusStringJNI_getString: strip the 4-byte header and footer,
// then use the device's original decoder with its format flag.
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    std::ifstream input(argv[1], std::ios::binary);
    if (!input) return 3;
    std::vector<char> bytes((std::istreambuf_iterator<char>(input)), {});
    if (bytes.size() < 9 || bytes[0] != 1) return 4;
    void *library = dlopen("/odm/lib64/libOplusSecurity.so", RTLD_NOW);
    if (!library) { fprintf(stderr, "%s\n", dlerror()); return 5; }
    auto decode = reinterpret_cast<char *(*)(char *, int, unsigned char)>(dlsym(library, "decode"));
    if (!decode) return 6;
    char *text = decode(bytes.data() + 4, static_cast<int>(bytes.size() - 8), bytes[1]);
    if (!text || (text[0] != '[' && text[0] != '{')) return 7;
    fputs(text, stdout);
    return 0;
}
