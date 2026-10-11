/* Test-only entry into the same arithmetic helper used by production source. */
#include "../src/function.c"
int32_t EP1_CDECL test_finish_byte_delta(uint32_t byte_delta)
{
    return finish_byte_delta(byte_delta);
}
