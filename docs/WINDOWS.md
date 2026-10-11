# Windows setup and contribution workflow

Use 64-bit Windows 10/11 and PowerShell. The game binaries are 32-bit; the host
Python, Clang, and JDK should be 64-bit. No client assets are needed for static
analysis or the first example. All commands below run from the repository root
unless stated otherwise.

## 1. Install Git, Python, and Clang

With WinGet:

```powershell
winget install --exact --id Git.Git
winget install --exact --id Python.Python.3.12
winget install --exact --id LLVM.LLVM
```

Reopen PowerShell so installers' PATH changes take effect. Check:

```powershell
git --version
py -3.12 --version
$env:Path = "$env:ProgramFiles\LLVM\bin;$env:Path"
clang --version
```

If WinGet is unavailable, use official [Git for Windows](https://gitforwindows.org/),
[Python](https://www.python.org/downloads/windows/), and
[LLVM](https://github.com/llvm/llvm-project/releases) installers. Install Python
3.12+ with its launcher and add LLVM's `bin` directory to PATH. The example uses
Clang's Windows x86 freestanding target; Visual Studio headers are not required.

## 2. Clone and verify

Choose a normal project directory:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\Projects" | Out-Null
Set-Location "$env:USERPROFILE\Projects"
git clone https://github.com/Spelunkern/shaiya-ep1-reconstruction.git
Set-Location shaiya-ep1-reconstruction
py -3.12 tools/reverse.py verify
py -3.12 tools/reverse.py audit --originals
```

Do not enable Git LFS or download client data for this workflow. Git attributes
keep text at LF and original binaries unchanged. Use paths without command-shell
metacharacters such as `%`, `!`, `&`, or `^` for Ghidra batch launches. If needed,
move the clone to a simple path such as `C:\Projects\shaiya-ep1-reconstruction`.

## 3. Run the first example

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r contributions/86424e839ec26fb4-fn-00001d80/tests/requirements.txt
& .\.venv\Scripts\python.exe contributions/86424e839ec26fb4-fn-00001d80/tests/differential.py
py -3.12 tools/reverse.py validate --block 86424e839ec26fb4-fn-00001d80
```

Expected result:

```text
PASS 3042 scan + 4 fault + 1022 arithmetic comparisons against original x86 instructions
```

Invoking `.venv\Scripts\python.exe` directly avoids activation and does not require
changing PowerShell execution policy. Results go to `work/first-block-test/`.
See [FIRST_BLOCK.md](FIRST_BLOCK.md) for comparison scope and limitations.

## 4. Install and use Ghidra

The installer downloads and verifies Ghidra 12.1.4 and the Windows JDK 21 package.
It uses `work/toolchain/` and does not replace system Java.

```powershell
py -3.12 tools/install_toolchain.py
$env:GHIDRA_HOME = Join-Path $PWD "work\toolchain\ghidra_12.1.4_PUBLIC"
$env:JAVA_HOME = Join-Path $PWD "work\toolchain\jdk-21.0.12.1+1"
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
& "$env:JAVA_HOME\bin\java.exe" -version
py -3.12 tools/reverse.py analyze --binary Client/CONFIG.exe
py -3.12 tools/reverse.py export 86424e839ec26fb4-fn-00001d80
```

The CLI selects `analyzeHeadless.bat` through `cmd.exe` and normalizes line endings
in fresh exports before comparing them with the unchanged published baseline.
The last command above is an evidence reproduction example; do not reserve that
already-submitted block. For your task use its own `BINARY_ID` and `BLOCK_ID`.

To open Ghidra's GUI:

```powershell
& "$env:GHIDRA_HOME\ghidraRun.bat"
```

Projects are in `work/ghidra/`. Preserve the canonical project; use a separate
copy for exploratory edits. Evidence is in `work/evidence/<block_id>/` and logs
are in `work/logs/`. A failed identity or reproduction check must be investigated
rather than bypassed by changing frozen files.

## 5. Reserve and contribute

Fork the repository on GitHub and clone your fork for submissions. Add upstream
if it is missing, then follow [CONTRIBUTING.md](../CONTRIBUTING.md). GitHub CLI is
optional and can be installed with `winget install --exact --id GitHub.cli`.
Use `gh auth login` if choosing that PR workflow; browser PRs are also supported.

After the reservation PR is accepted:

```powershell
git fetch upstream
git switch -c reverse/BLOCK_ID upstream/main
py -3.12 tools/reverse.py start BLOCK_ID --owner GITHUB_USER
New-Item -ItemType Directory -Force work | Out-Null
py -3.12 tools/reverse.py prompt BLOCK_ID --owner GITHUB_USER | Set-Content -Encoding utf8 work/task.md
```

Give the generated prompt to your agent in the fork root. Reconstruct, test, and
submit only that reserved scope. Use English, preserve notices, and contribute
project-authored work under BSD-3-Clause. Ready submissions require independent review.

## 6. Check a binary ZIP download

The repository clone already contains the binaries. If restoring them from a
release ZIP, download `binaries-bundle.json` too and compare before extraction:

```powershell
$manifest = Get-Content .\binaries-bundle.json -Raw | ConvertFrom-Json
$actual = (Get-FileHash .\shaiya-ep1-binaries.zip -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $manifest.sha256) { throw "Binary ZIP checksum mismatch" }
Expand-Archive .\shaiya-ep1-binaries.zip -DestinationPath . -Force
py -3.12 tools/reverse.py verify
```

Only use the manifest downloaded from the same official release. Original binary
licenses are separate from the project BSD license; read `NOTICE.md`.
