# First block: length of 16-bit units

Block `86424e839ec26fb4-fn-00001d80` belongs to `Client/CONFIG.exe`.
Original SHA-256:
`86424e839ec26fb454cd343c451200e290cf528a88b53c2e77e7407573dac844`.
Entry RVA `0x1d80`, VA `0x00401d80`; body `[0x1d80,0x1d96)`, 22 bytes.
Body digest:
`ab4bab194aae7751eae686a11b9b3777dd65c29138d9a7d064cc8a88cb137299`.

## Evidence and interpretation

| Address | Evidence | Consequence |
|---|---|---|
| `00401d80` | `MOV EAX,[ESP+4]` | First argument is a stack pointer value |
| `00401d84` | 16-bit `MOV CX,[EAX]` | Reads one two-byte unit |
| `00401d87`, `00401d88` | Two `INC EAX` instructions | Advances two bytes per iteration |
| `00401d89`, `00401d8c` | `TEST CX,CX; JNZ 00401d84` | Continues through the first zero unit |
| `00401d8e` | `SUB EAX,[ESP+4]` | Byte distance uses 32-bit arithmetic |
| `00401d92`, `00401d94` | `SAR EAX,1; DEC EAX` | Converts distance and excludes terminator |
| `00401d95` | `RET` without immediate | Caller cleans the argument |
| Caller `00401bee`, `00401bf3` | `CALL 00401d80; ADD ESP,4` | Confirms four-byte caller cleanup |

For ordinary strings, the return is the number of nonzero 16-bit units. This
counts units, not Unicode code points; a surrogate pair contributes two and UTF-16
is not validated. No null check or length bound exists. Input must remain readable
through the terminator. The caller uses the result to search a word buffer for
`0x005c`, as shown in `original/callers.txt`.

The original name is not assumed to be wcslen. The binary/RVA symbol is retained.
Ghidra signatures are hints; `const void *` represents unaligned inputs as well.

## Source decisions

A fixed two-byte intrinsic copy permits unaligned input. The tested Windows x86
builds perform 16-bit reads without new imports. An unsigned byte counter preserves
32-bit modular distance. `finish_byte_delta` reproduces SAR and DEC without signed
C overflow. The source avoids platform-dependent wchar_t and an incorrect unsigned
replacement for arithmetic shift.

The catalog records no dependencies: the original has no calls or global accesses.
Internal source helpers belong to this implementation; they are not additional
functions recovered from the original.

## Executed comparisons

`tests/differential.py` builds i386 Windows COFF at `-O0` and `-O2`. It loads machine
code and applies only REL32 relocations within .text; external dependencies fail.
The compiled function and original 22 bytes receive the same ABI inputs.

**4,068 comparisons passed:** 3,042 scans, four invalid-input faults, and 1,022
arithmetic-tail cases. Tests check EAX, ESP, argument preservation, nonvolatile
registers, unchanged input, and exact read addresses/widths. Cases include empty
input, surrogate/high units, embedded zeros, odd alignment, guard-page terminators,
and deterministic randomized inputs.

Fault comparisons check access type/address/width and previous reads. EAX is not
compared on fault because no defined return occurred and it is volatile. Large
deltas are tested by entering original SUB/SAR/DEC/RET with synthetic register
state, without claiming a multi-gigabyte string was fully scanned.

Logs and environment are under `logs/` and `proof.json`. Status is **ready** for
independent review; there is no review record or complete CONFIG.exe rebuild.
Project-authored source uses BSD-3-Clause; original evidence retains its own rights.
