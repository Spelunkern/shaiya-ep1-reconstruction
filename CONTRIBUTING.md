# Contribute a block with an AI agent

The upstream repository is [Spelunkern/shaiya-ep1-reconstruction](https://github.com/Spelunkern/shaiya-ep1-reconstruction).
Original binaries are included. The [first block](docs/FIRST_BLOCK.md) is a real
submission with reproducible tests. Windows users should start with
[WINDOWS.md](docs/WINDOWS.md); commands below use Git and Python from the repository root.

## 1. Prepare a fork

Fork on GitHub and clone your fork. GitHub CLI can do both:

```bash
gh repo fork Spelunkern/shaiya-ep1-reconstruction --clone
cd shaiya-ep1-reconstruction
git remote -v
# Add upstream only if gh did not already create it:
git remote add upstream https://github.com/Spelunkern/shaiya-ep1-reconstruction.git
```

Check the remotes before adding a duplicate. On Windows, use `py -3.12` in place
of `python` below, or use the Python executable from your virtual environment.

```bash
python tools/reverse.py verify
python tools/reverse.py audit --originals
python tools/reverse.py list --kind function --available --max-instructions 30 --limit 20
python tools/reverse.py show BLOCK_ID
```

Choose few instructions and dependencies initially. `--available` excludes
reservations, existing submissions, and unresolved direct flow. A short function
may still be a thunk or depend on complex contracts. The example is already submitted.

## 2. Obtain an accepted reservation

Replace `BLOCK_ID` with the exact catalog ID and `GITHUB_USER` with your account.

```bash
git fetch upstream
git switch -c claim/BLOCK_ID upstream/main
python tools/reverse.py claim BLOCK_ID --owner GITHUB_USER
git add claims/BLOCK_ID.json
git commit -m "Reserve BLOCK_ID"
git push -u origin HEAD
```

Open a PR against upstream/main containing only the reservation. With GitHub CLI:

```bash
gh pr create --repo Spelunkern/shaiya-ep1-reconstruction --base main --title "Reserve BLOCK_ID" --body "Reservation for GITHUB_USER"
```

Wait for the reservation PR to merge before reconstructing. File creation is
exclusive within a clone; it is not a lock across clones. The accepted upstream
reservation is authoritative. Issues can coordinate work but do not replace it.
Reservations expire after seven days; renewal or reassignment requires review.
Delivered blocks do not become available when a reservation expires.

## 3. Start the reserved task

After the reservation merges:

```bash
git fetch upstream
git switch -c reverse/BLOCK_ID upstream/main
python tools/reverse.py start BLOCK_ID --owner GITHUB_USER
```

Create `work/` and generate the exact agent prompt. Linux:

```bash
mkdir -p work
python tools/reverse.py prompt BLOCK_ID --owner GITHUB_USER > work/task.md
```

PowerShell:

```powershell
New-Item -ItemType Directory -Force work | Out-Null
py -3.12 tools/reverse.py prompt BLOCK_ID --owner GITHUB_USER | Set-Content -Encoding utf8 work/task.md
```

Open your agent in the fork root and provide `work/task.md`. Follow
[the agent guide](docs/AGENT_GUIDE.md). Install the pinned tools using the relevant
OS guide, then run:

```bash
python tools/reverse.py analyze --binary BINARY_ID
python tools/reverse.py export BLOCK_ID
```

A fresh clone regenerates the Ghidra project and must reproduce the frozen export.
If it differs, preserve logs and propose a diagnosis; do not rewrite the catalog.
Inspect non-function blocks by their ranges in Ghidra.

## 4. Complete the submission

Keep all block work in `contributions/<block_id>/`:

```text
submission.json
analysis.md
src/...
include/...
original/listing.txt
original/decompiled.c
proof.json
logs/build.log
logs/comparison.log
tests/...
```

Document evidence by address, ABI, layouts, effects, and contracts for every catalog
dependency. Investigate indirect calls and unresolved references. Decompiled C
belongs to evidence, not production source.

Tests must compare against original evidence and detect deviations, including edge
conditions. Retain real commands, versions, logs, and comparison limits. Host x64
logic tests alone do not validate Windows x86 ABI. Do not fill production gaps with stubs.
Declare every relevant source, test, and evidence file in `submission.json`.
Coordinate shared type changes and their consumers separately.

## 5. Submit for review

Use `draft` while contracts or verification are incomplete. Use `ready` only when
`docs/PROTOCOL.md` is satisfied and `unknowns` is empty. It is not an approval.

```bash
python tools/reverse.py validate --block BLOCK_ID
# Also execute your block's actual test command.
git add contributions/BLOCK_ID
git commit -m "Reconstruct BLOCK_ID"
git push -u origin HEAD
gh pr create --repo Spelunkern/shaiya-ep1-reconstruction --base main
```

Complete the PR template with behavior, baseline, ABI, tests, and limitations.
Each block needs its own reservation and submission. Do not include generated
`work/` files, modified originals, or self-reviews. An independent reviewer
reproduces results; maintainer acceptance on main makes the review official.
Changes to a submission invalidate previous review digests.

## License

Submit project-authored contributions under [BSD-3-Clause](LICENSE), retaining
applicable copyright and third-party notices. See [NOTICE.md](NOTICE.md) for the
scope of the license and treatment of original materials.
