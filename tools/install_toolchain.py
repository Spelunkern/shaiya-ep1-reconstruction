#!/usr/bin/env python3
"""Install checksum-pinned Ghidra/JDK locally on Linux or Windows x86_64 (Python 3.12+)."""
import hashlib
import json
from pathlib import Path
import platform
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    if platform.system() not in ('Linux', 'Windows') or platform.machine().lower() not in ('x86_64', 'amd64'):
        raise SystemExit('This installer supports Linux and Windows x86_64; see docs/TOOLCHAIN.md.')
    vendor = ROOT / 'work/toolchain'
    vendor.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / 'manifests/toolchain.json').read_text())
    if platform.system() == 'Windows':
        lock = json.loads((ROOT / 'manifests/platform-tools.json').read_text())['windows_x86_64']
    for item in lock['packages']:
        archive = vendor / item['name']
        if not archive.exists():
            partial = archive.with_name(archive.name + '.part')
            print(f'Downloading {archive.name}', flush=True)
            request = urllib.request.Request(item['url'], headers={'User-Agent':'ShaiyaEP1Reconstruction/1'})
            with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as f:
                while chunk := response.read(1024 * 1024):
                    f.write(chunk)
            partial.replace(archive)
        with archive.open('rb') as f:
            if hashlib.file_digest(f, 'sha256').hexdigest() != item['sha256']:
                raise ValueError(f'Checksum mismatch: {archive.name}')
        if not (vendor / item['directory']).exists():
            if archive.suffix == '.zip':
                with zipfile.ZipFile(archive) as z:
                    for entry in z.infolist():
                        destination = (vendor / entry.filename).resolve()
                        if not destination.is_relative_to(vendor.resolve()):
                            raise ValueError('Archive path traversal')
                    z.extractall(vendor)
                    for entry in z.infolist():
                        mode = entry.external_attr >> 16
                        if mode & 0o111:
                            (vendor / entry.filename).chmod(mode & 0o777)
            else:
                with tarfile.open(archive) as t:
                    t.extractall(vendor, filter='data')
        print(f'Installed {item["directory"]}', flush=True)
    print('Set GHIDRA_HOME and JAVA_HOME as shown in docs/TOOLCHAIN.md')

if __name__ == '__main__':
    main()
