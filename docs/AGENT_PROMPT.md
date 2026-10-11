# Prompt for an AI agent

Generate it with `python tools/reverse.py prompt BLOCK_ID --owner GITHUB_USER`.
On Windows use `py -3.12`. The command resolves `BINARY_ID`, the original path,
full SHA-256, and baseline. When copying manually, replace all three placeholders
with an accepted reservation and its binary. Run from the repository root.

```text
Reconstruct block BLOCK_ID for GITHUB_USER.

1. Read AGENTS.md, README.md, CONTRIBUTING.md, docs/PROTOCOL.md, and
   docs/AGENT_GUIDE.md. Use docs/FIRST_BLOCK.md as a format reference.
   On Windows also read docs/WINDOWS.md. Confirm the reservation in claims/
   belongs to GITHUB_USER, is unexpired, and is accepted in upstream/main.
2. Run show for the block, verify, and audit --originals. Identify the full
   original SHA-256, baseline, entry RVA, and every body range.
   Use image_base + RVA for Ghidra addresses. Preserve original binary bytes.
3. Use start if the submission directory does not exist. If the local Ghidra
   project is missing, use analyze --binary BINARY_ID. For functions, use export
   and examine all body instructions, callers, callees, data, and pseudocode.
   For other block kinds, inspect their ranges and obligations.
4. Reconstruct behavior and record evidence by address in analysis.md.
   Determine calling convention, parameters, return, layouts, globals, effects,
   errors, and edge behavior. Distinguish observations from hypotheses.
   Investigate indirect calls, unresolved references, and external contracts.
5. Write maintainable source only for the assigned scope. Resolve types and
   semantics rather than copying pseudocode. Use binary/RVA symbols, preserve
   Windows x86 ABI, and reuse accepted contracts. Do not invent dependencies
   or implement other blocks. Request coordination for missing shared contracts.
6. Create tests that detect differences from original instructions or recorded
   original observations. Include edge conditions and observable effects.
   Run feasible comparisons; keep commands, environments, and logs. Do not report
   unexecuted tests as passing or confuse portable tests with ABI validation.
7. Complete submission.json with source, test, and evidence files, ABI, contracts,
   and unknowns. Keep draft while evidence or verification is incomplete; use
   ready only when the protocol is satisfied. Run validate --block BLOCK_ID.
8. Report behavior, files, actual tests, and limits. Use English and BSD-3-Clause
   for project-authored work; retain applicable notices. Do not approve your own
   submission or publish a PR without authorization for that action.

Persist with authorized analysis. If a dependency blocks progress, finish the
independent evidence and record exactly what is missing. Written code volume
is not evidence of equivalence.
```
