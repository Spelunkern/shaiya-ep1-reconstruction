# Identity, submission, and acceptance

## Work identity

The baseline binds the historical inventory, exporter, partition algorithm,
Ghidra version, and export hashes. Every block, claim, and submission carries
`baseline_id`; the catalog has a separate checksum.

Function IDs are `<binary_id>-fn-<entry_rva>`. Ranges are sorted, half-open RVAs
`[start, end)` and may be discontinuous. The body digest is SHA-256 of bytes
concatenated in range order. Do not cut functions to balance workloads.
Initial references are partial evidence, not a complete callback or indirect-call graph.

| Kind | Expected work |
|---|---|
| `function` | Reconstructed source and function contract |
| `data` | Globals, tables, structures, resources, or padding; reproducible definitions |
| `unclassified` | Determine code, data, padding, or opaque content with evidence |
| `integration` | File headers/overlays, imports/exports, resources, relocations, ABI, and whole-binary build |

Data and unknown regions use inspection tasks of at most 64 KiB. This is not a
claim of semantic independence. Coordinate tables spanning multiple tasks.
Virtual zero-fill belongs to the PE image, not necessarily the file. Integration
blocks record file intervals outside sections, including headers and overlays.

Direct flow to a target without a known function entry requires boundary review
before reservation. An interior jump can hide a shared tail even when Ghidra
body ranges do not overlap. `--available`, `claim`, and `start` exclude these cases.
Discovering entries or changing ownership requires a baseline migration.
Shared bodies are recorded in `blocks/baseline.json` and blocked for ordinary
reservations. Unclassified padding and resources remain pending work.

## Contracts and integration

Use `ep1_<binary_id>_<rva>` for functions and `data_<rva>` for data; document
semantic names as aliases. C or C++ is allowed as evidence warrants.
Do not accept Ghidra's default calling convention without caller/stack evidence.
Document widths, offsets, alignment, padding, signedness, ownership, and lifetime.
Shared type changes must identify every consumer. The catalog records known
entry call/jump dependencies and static data references; document additional
contracts and edges discovered during reconstruction with evidence.

Integrators keep one implementation per symbol under `reconstruction/<binary_id>/`
and maintain a symbol-to-block map. Missing production implementations must fail
the build rather than being replaced with stubs. Original compiler and environment
remain to be identified. Identical DLLs are built once and installed at each
inventoried path. Whole-system integration will need separately defined test data.

## Submission and review states

Contributors use `draft` or `ready`. Ready requires source, evidence, tests,
analysis, dependency contracts, empty `unknowns`, and a function ABI where applicable.
Structural validation does not execute arbitrary submission commands or certify
semantic correctness.

Independent review stages are:

1. `source_reviewed`: manual source/instruction/contract comparison.
2. `block_validated`: build and original comparison with commands and logs.
3. `integrated`: whole-binary integration tests with documented scope and limits.

The reviewer reproduces results and declares `proof.json` in `evidence_files`:

```json
{
  "environment": "Exact OS, architecture, compiler, flags, and harness",
  "reasoning": "Equivalence checked and its limits",
  "build": {"result": "pass", "command": "ACTUAL_COMMAND", "log": "logs/build.log"},
  "comparison": {
    "result": "pass",
    "command": "ACTUAL_COMMAND",
    "log": "logs/comparison.log",
    "original_sha256": "FULL_ORIGINAL_BINARY_SHA256",
    "method": "Reproducible execution, emulation, or instruction proof",
    "cases": ["Actual cases and verified edge conditions"]
  },
  "limitations": ["Specific limits of the comparison"]
}
```

For `integrated`, also provide `integration` with `result`, `command`, and a
declared log for the whole binary. Record the review using:

```bash
python tools/reverse.py review BLOCK_ID --reviewer REVIEWER --stage block_validated --proof proof.json
python tools/reverse.py validate
```

The review binds source, tests, analysis, and evidence digests. Changes invalidate
it. A JSON reviewer name is not authentication; independent review and maintainer
acceptance on the protected main branch make it official. Do not modify others'
claims or introduce self-reviews. CI has no repository secrets and checks original
identity, distribution, coverage, submissions, and isolated function comparisons.

Track classified regions, reviewed source, validated blocks, integration, and
system tests separately. Byte-identical builds additionally require reproducing
layout, toolchain, and options. Finite tests are not a universal equivalence proof.

## Baseline migration

Corrected boundaries, hidden code, or repartitioning require a new baseline.
Do not renumber existing work in place. Preserve the previous version, publish an
`old_id -> new_id` map, review affected claims/submissions, and rerun coverage and
body checks. The CLI rejects overwriting frozen inventory or plans. Platform-only
launch support normalizes line endings in new scratch exports before comparing
against the unchanged published baseline.
