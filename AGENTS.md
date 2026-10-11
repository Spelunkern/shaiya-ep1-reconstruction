# Repository instructions for AI agents

Read `README.md`, `CONTRIBUTING.md`, `docs/PROTOCOL.md`, `docs/AGENT_GUIDE.md`,
and `docs/AGENT_PROMPT.md` before working. All project-authored documentation,
comments, prompts, templates, and user-facing text must be in English.

## Scope and evidence

- Work only on assigned blocks reserved to the contributor in upstream/main.
  Verify the block ID, baseline, and full binary SHA-256 before interpreting code.
- Preserve original binaries. Static analysis does not execute or patch them.
  Authorized dynamic comparisons use isolated copies, synthetic inputs, and
  recorded commands. Do not run services against real databases or accounts.
- `analysis/baseline/`, `blocks/`, and `manifests/originals.json` are frozen.
  Do not rewrite them to accommodate a submission. Propose an evidenced migration.
- Ghidra pseudocode is evidence, not an implementation or proof. Infer signatures,
  types, offsets, flow, exceptions, and effects from instructions and observations.
  Record uncertainties in `submission.json`.
- Do not invent original names, layouts, algorithms, dependencies, or test results.
  Use binary/RVA identifiers until evidence supports a semantic alias.
- Do not create production stubs. Explicit test doubles must be separate from
  production source and have documented contracts.
- Shared bodies and unresolved outgoing direct flow require boundary coordination
  before normal reservations. Investigate indirect calls, callbacks, and tail jumps.

## Submissions

- Keep work in `contributions/<block_id>/`. Propose shared contract changes
  separately, naming every affected consumer.
- Preserve Windows x86 calling conventions, widths, signedness, alignment, effects,
  and edge behavior. A Linux x64 logic build does not validate the Windows x86 ABI.
- Record commands, environments, and actual results. Never report unexecuted tests
  as passing. Keep incomplete evidence or verification in `draft`.
- `ready` means ready for independent review. Contributors and their agents must
  not approve their own blocks or create self-reviews under `reviews/`.
- Run `python tools/reverse.py validate --block <block_id>` and relevant block
  tests. Infrastructure changes require the repository tests.
- Create external PRs only when the user has authorized that submission. Do not
  message others or delegate to other agents without explicit authorization.
- Project-authored work and contributions use BSD-3-Clause. Preserve attribution
  and follow `LICENSE` and `NOTICE.md`; original binaries are not relicensed.

## Infrastructure and distribution

Python 3.12+, Ghidra 12.1.4, and JDK 21 are required for analysis. See
`docs/WINDOWS.md` for PowerShell and `docs/TOOLCHAIN.md` for Linux.
Ghidra projects are in `work/ghidra/` and must not be overwritten.
Changes to the frozen partition algorithm require an explicit baseline migration.

Git distributes only the PE paths in `manifests/public-binaries.json`. Do not add
client assets, original databases, configurations, or logs. `verify` checks the
public binaries; `--full-corpus` is for the private historical corpus only.
`bundle` creates the binary ZIP and licensing notices. The first example and
its reproducible comparisons are documented in `docs/FIRST_BLOCK.md`.
