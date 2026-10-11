# First complete example block

The example is [86424e839ec26fb4-fn-00001d80](../contributions/86424e839ec26fb4-fn-00001d80/),
a CONFIG.exe function at VA `0x00401d80`: 22 bytes and ten instructions. It scans
16-bit little-endian units through zero. This is a real corpus block with source,
ABI, original evidence, and comparisons against actual original instructions.

Read its [address-based analysis](../contributions/86424e839ec26fb4-fn-00001d80/analysis.md),
[C source](../contributions/86424e839ec26fb4-fn-00001d80/src/function.c),
[submission](../contributions/86424e839ec26fb4-fn-00001d80/submission.json), and
[results](../contributions/86424e839ec26fb4-fn-00001d80/logs/comparison.json).

## Linux x86_64

Install Python 3.12+, venv support, and Clang. Ubuntu/Debian, if missing:

```bash
sudo apt-get update
sudo apt-get install clang python3-venv
```

From the clone root:

```bash
python3 tools/reverse.py verify
python3 -m venv .venv
.venv/bin/python -m pip install -r contributions/86424e839ec26fb4-fn-00001d80/tests/requirements.txt
.venv/bin/python contributions/86424e839ec26fb4-fn-00001d80/tests/differential.py
python3 tools/reverse.py validate --block 86424e839ec26fb4-fn-00001d80
```

## Windows x86_64

Install the tools as described in [WINDOWS.md](WINDOWS.md). In PowerShell:

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r contributions/86424e839ec26fb4-fn-00001d80/tests/requirements.txt
& .\.venv\Scripts\python.exe contributions/86424e839ec26fb4-fn-00001d80/tests/differential.py
py -3.12 tools/reverse.py validate --block 86424e839ec26fb4-fn-00001d80
```

Both platforms should print:

```text
PASS 3042 scan + 4 fault + 1022 arithmetic comparisons against original x86 instructions
```

New objects and results go to `work/first-block-test/`; submitted logs remain
unchanged. The test checks original binary and body SHA-256 before emulation.
No client assets, game server, or whole CONFIG.exe execution are required.

## Evidence and limits

Clang builds `i686-pc-windows-msvc` COFF; Unicorn 2.1.4 emulates x86-32. Tests compare
compiled source with original bytes, not another pseudocode translation. They
check ABI, return, and exact input reads at two optimization levels, including
adversarial inputs and synthetic arithmetic-tail overflow cases.
See [Clang](https://clang.llvm.org/docs/CrossCompilation.html) and
[Unicorn](https://www.unicorn-engine.org/docs/tutorial.html) for the interfaces.

This does not establish byte-identical builds or whole-executable equivalence.
Specific limits are recorded in the proof. The submission is `ready`, pending
independent review, and has no self-approval record.

## Use as a submission template

Reserve another available block. Copy the structure, not hashes, results, or ABI.
Provide your own evidence and an appropriate harness for callbacks, globals,
WinAPI, or network contracts. Test doubles never fill production gaps.
Follow [CONTRIBUTING.md](../CONTRIBUTING.md), generate your exact prompt with
`reverse.py prompt`, and use BSD-3-Clause for project-authored source.
