# Public binary distribution

Git directly includes 27 original PE paths, representing 23 unique binaries,
under `Client/` and `Server/`. No Git LFS or external client assets are needed.
Binary file sizes total **20,910,273 bytes**.

```bash
git clone https://github.com/Spelunkern/shaiya-ep1-reconstruction.git
cd shaiya-ep1-reconstruction
python tools/reverse.py verify
```

On Windows use `py -3.12`; see [WINDOWS.md](WINDOWS.md). Verification defaults to
published PE paths and checks size/SHA-256. `manifests/public-binaries.json` defines
exact distribution scope. GameGuard.des is included because it is PE regardless
of extension. Identical DLLs share IDs; full SHA-256 remains authoritative.

## Binary-only download

[Release v0.1.1](https://github.com/Spelunkern/shaiya-ep1-reconstruction/releases/tag/v0.1.1)
provides `shaiya-ep1-binaries.zip`, `binaries-bundle.json`, and `SHA256SUMS`.
The ZIP contains the PE files, public manifest, and licensing notices. Original
binaries are not relicensed by the project BSD license; see [NOTICE.md](../NOTICE.md).

Regenerate from a verified clone with `python tools/reverse.py bundle`.
The command uses an explicit PE allowlist and does not include other local
Client/Server files. Outputs are under `dist/`. Move an existing generated bundle
aside before rebuilding. On Linux verify downloads with `sha256sum -c SHA256SUMS`;
Windows has `Get-FileHash` commands in its guide. Then use `verify` after extraction.

## Private historical corpus

Client data.saf/data.sah, external maps, original databases, configurations, and
logs are excluded. The maintainer's original folders remain intact locally;
`tools/check_distribution.py` prevents other originals from being tracked under
those folders.

`manifests/originals.json` preserves the historical 394-file inventory because it
participates in the frozen baseline. It records paths and hashes, not file contents.
Only maintainers with that complete private corpus use `verify --full-corpus`.
Contributors do not need those files. Whole-system integration will require
separately defined test data beyond this static-analysis corpus.
