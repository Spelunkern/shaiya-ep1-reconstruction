#ifndef EP1_86424E839EC26FB4_00001D80_H
#define EP1_86424E839EC26FB4_00001D80_H
#include <stdint.h>
#if defined(_MSC_VER) || defined(__i386__)
#define EP1_CDECL __cdecl
#else
#define EP1_CDECL
#endif
#ifdef __cplusplus
extern "C" {
#endif
/* Reads 16-bit little-endian units through the first zero unit. */
int32_t EP1_CDECL ep1_86424e839ec26fb4_00001d80(const void *text);
#ifdef __cplusplus
}
#endif
#endif
