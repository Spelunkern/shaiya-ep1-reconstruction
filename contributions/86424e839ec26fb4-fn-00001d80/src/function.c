#include "../include/function.h"

/* Preserve the original SUB/SAR/DEC result, including 32-bit wraparound. */
static inline int32_t finish_byte_delta(uint32_t byte_delta)
{
    uint32_t shifted = (byte_delta >> 1) | (byte_delta & UINT32_C(0x80000000));
    uint32_t result_bits = shifted - UINT32_C(1);
    if (result_bits <= INT32_MAX)
        return (int32_t)result_bits;
    return -1 - (int32_t)(UINT32_MAX - result_bits);
}

int32_t EP1_CDECL ep1_86424e839ec26fb4_00001d80(const void *text)
{
    const unsigned char *cursor = (const unsigned char *)text;
    uint32_t byte_delta = 0;
    uint16_t unit;
    do {
        /* Fixed-size memcpy allows an unaligned input; x86 is little-endian. */
        __builtin_memcpy(&unit, cursor, sizeof(unit));
        cursor += sizeof(unit);
        byte_delta += sizeof(unit);
    } while (unit != 0);
    return finish_byte_delta(byte_delta);
}
