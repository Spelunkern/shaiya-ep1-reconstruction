# Initial corpus analysis

Baseline generated on **October 11, 2026**, with Ghidra 12.1.4 and JDK 21.
Original programs were not executed during inventory or static auto-analysis.

```text
baseline_id: 7c4fe1157c5b3af787cf27c11ff47ab2903b30f627ede2e9b4a81fea1b7e057a
```

The historical corpus has 394 files, 27 PE paths, and 23 unique binaries. Four
redundant PE paths are identical dbgeng.dll/dbghelp.dll copies. Public distribution
contains only those PE binaries, without external client data.

| Block kind | Count |
|---|---:|
| Detected functions | 45,259 |
| Data/resources | 1,495 |
| Unclassified executable regions | 33,443 |
| Per-binary integration | 23 |
| Total | 80,220 |

**94 functions need boundary or direct-flow review** and are excluded from ordinary
reservations. Exported body ranges do not overlap; this does not rule out shared
tails assigned by Ghidra to one function.

## Analysis coverage

Function bodies occupy 8,045,885 of 10,352,640 bytes in executable sections,
approximately 77.72%. This is not a reconstructed-source percentage. Remaining
executable bytes have classification tasks; data and file intervals outside
sections also have assigned work. Coverage tests check these PE areas for gaps.

| Primary binary path | Functions | Executable bytes assigned to bodies | Pending executable bytes |
|---|---:|---:|---:|
| `Client/CONFIG.exe` | 88 | 90.58% | 1,881 |
| `Client/GameGuard.des` | 1 | 0.11% | 433,689 |
| `Client/Updater.exe` | 2,445 | 88.91% | 31,801 |
| `Client/game.exe` | 7,116 | 81.65% | 361,469 |
| `Client/ijl15.dll` | 406 | 70.35% | 94,733 |
| `Client/zlib.dll` | 154 | 90.52% | 3,739 |
| `Server/PSM_Client/Bin/dbgeng.dll` | 6,179 | 79.91% | 439,151 |
| `Server/PSM_Client/Bin/dbghelp.dll` | 5,390 | 82.73% | 149,554 |
| `Server/PSM_Client/Bin/ggauth.dll` | 627 | 81.11% | 9,286 |
| `Server/PSM_Client/Bin/ggauth53.dll` | 706 | 95.75% | 6,961 |
| `Server/PSM_Client/Bin/ggauth54.dll` | 560 | 95.50% | 5,900 |
| `Server/PSM_Client/Bin/ggauth55.dll` | 512 | 93.97% | 7,160 |
| `Server/PSM_Client/Bin/ggauth60.dll` | 629 | 85.94% | 11,520 |
| `Server/PSM_Client/Bin/ggsrvdll.dll` | 174 | 93.64% | 1,824 |
| `Server/PSM_Client/Bin/ps_dbAgent.exe` | 1,571 | 79.57% | 70,281 |
| `Server/PSM_Client/Bin/ps_game.exe` | 3,438 | 82.57% | 156,349 |
| `Server/PSM_Client/Bin/ps_gameLog.exe` | 1,247 | 77.71% | 53,859 |
| `Server/PSM_Client/Bin/ps_login.exe` | 1,327 | 76.68% | 60,167 |
| `Server/PSM_Client/Bin/ps_session.exe` | 1,314 | 77.31% | 58,559 |
| `Server/PSM_Client/Bin/ps_userLog.exe` | 1,226 | 77.31% | 52,036 |
| `Server/PSM_Client/PSM_Agent.exe` | 2,806 | 78.49% | 88,096 |
| `Server/PSM_Server/PSMServer_Agent.exe` | 2,804 | 79.15% | 84,536 |
| `Server/PSM_Server/PSMServer_Mgr.exe` | 4,539 | 79.78% | 124,204 |

Coverage includes padding and virtual image ranges and does not estimate missing
real instructions. There are 25,669 unclassified blocks of at most 16 bytes.
Many may be alignment, but classification is not presumed. Coordinated batches
can retain individual reservations and submissions.

## Findings and priorities

- Client/game.exe has 7,116 detected functions. Establish object, global,
  callback, and ABI contracts before reconstructing consumers.
- ps_game.exe has 3,438 functions. Establish session, message, and data-access
  contracts from instruction evidence.
- GameGuard.des has one function and 0.11% executable-byte coverage. Its .text
  has no raw file bytes, suggesting runtime-prepared content. It needs loading
  or packing investigation; complete code discovery has not been demonstrated.
- Third-party DLLs have their own catalogs. Available source may help after
  proving version correspondence, binary compatibility, and applicable notices.

Observed example `86424e839ec26fb4-fn-000032d0` contains three body instructions,
including a transfer to 0x00403345. Its decompilation shows a string-copy algorithm
outside that body. The unresolved destination blocks reservation pending boundary
review. A small body and readable pseudocode do not establish independent scope.

## Bootstrap verification

- All 23 exports completed without analysis timeout.
- Every one of the 45,259 function body hashes matches original bytes, with
  virtual zero-fill represented where applicable.
- CONFIG.exe was regenerated in a fresh project and its exports matched byte
  for byte. Individual evidence export checked project identity and body digest.
- Tests cover section/file coverage, submission identity, path escape, contracts,
  stale review rejection, and reservation conflicts.
- The public binary ZIP has per-file identity and an archive checksum.

[diagnostics.json](../analysis/diagnostics.json) summarizes original warnings;
full local logs are in work/logs/. Successful analysis can still contain type,
resource, or boundary errors. This baseline is an initial work map.

**At baseline creation: zero accepted blocks and zero rebuilt binaries.**
The subsequent [first example](FIRST_BLOCK.md) is a real ready submission with
passing comparisons, pending independent review. Use `reverse.py report` for
current status. The 394-file inventory is historical; contributors need only the
27 distributed PE paths. Documentation and tooling use English and BSD-3-Clause
within the scope described in NOTICE.md.
