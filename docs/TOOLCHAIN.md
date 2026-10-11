# Toolchain and reproduction

Analysis is pinned to **Ghidra 12.1.4** and **JDK 21**. Python 3.12+ and the standard
library support the CLI. `manifests/toolchain.json` records the initial Linux
packages and remains frozen; `manifests/platform-tools.json` adds the Windows JDK.
Each download has an official URL and SHA-256. Use the pinned versions to reproduce
boundaries. See [WINDOWS.md](WINDOWS.md) for native PowerShell instructions.

## Linux x86_64

```bash
python3 tools/install_toolchain.py
export GHIDRA_HOME="$PWD/work/toolchain/ghidra_12.1.4_PUBLIC"
export JAVA_HOME="$PWD/work/toolchain/jdk-21.0.12.1+1"
python3 tools/reverse.py analyze --binary Client/game.exe
```

Existing pinned installations can be selected with these variables or `--ghidra`
and `--jdk`. The installer verifies packages before extraction and does not change
system Java. Analysis of every unique binary uses `python3 tools/reverse.py analyze`.

Imports use Ghidra's PE loader and auto-analysis, four CPUs, and 1,800 seconds per
file. Exports record language, compiler spec, image base, hash, count, and timeout.
Timeout prevents acceptance; success does not prove all boundaries are correct.
Inspect analyzer warnings and evidence independently.

Projects are `work/ghidra/<binary_id>.gpr`; logs are `work/logs/` and published
exports are `analysis/baseline/<binary_id>/`. Preserve incomplete projects and
logs, then move them into a diagnostic directory before retrying. Use separate
project copies for exploratory annotations rather than changing the canonical project.

## Windows x86_64

The same installer selects a checksum-pinned Windows JDK ZIP. The CLI uses
`analyzeHeadless.bat` through the Windows command processor and `java.exe`.
Line endings in newly generated exports are normalized to LF before comparing
against the frozen Linux baseline. Git attributes keep project text files at LF.
The Windows CI job exercises the example and regeneration of the CONFIG baseline.

Other architectures are not covered by the installer; select suitable official
JDK 21 builds manually and verify reproduction before asserting compatibility.

## Official references

See [Ghidra headless options](https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/RuntimeScripts/support/analyzeHeadlessREADME.md),
[Ghidra 12.1.4](https://github.com/NationalSecurityAgency/ghidra/releases/tag/Ghidra_12.1.4_build),
and [Temurin JDK 21](https://github.com/adoptium/temurin21-binaries/releases).
