#!/usr/bin/env python3
"""Generiert packages.json aus allen PKGBUILD-Unterordnern."""

import json
import shlex
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/astrapi/packages_archlinux.git"

# Trennzeichen ausserhalb des druckbaren ASCII-Bereichs, damit es garantiert
# nicht in pkgname/pkgver/pkgrel/pkgdesc auftaucht.
_SEP = "\x1e"


def parse_pkgbuild(path: Path) -> dict:
    """Liest pkgname/pkgver/pkgrel/pkgdesc, indem das PKGBUILD per Bash
    tatsaechlich ausgewertet wird (source ...) statt per Regex den Text
    zu durchsuchen -- reine Text-Extraktion scheitert an ganz normalen
    Arch-Konventionen wie pkgname="$_pkgname"-ltr (Suffix-Varianten wie
    -ltr/-git/-bin). Die PKGBUILDs in diesem Repo fuehren auf oberster
    Ebene keine Befehle aus (nur Variablen/Arrays, Arbeit passiert in
    prepare()/build()/package()), Sourcing ist daher unbedenklich.
    """
    script = (
        f"source {shlex.quote(str(path))}\n"
        f'printf "%s{_SEP}%s{_SEP}%s{_SEP}%s\\n" '
        '"$pkgname" "$pkgver" "$pkgrel" "$pkgdesc"'
    )
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True,
        text=True,
        cwd=path.parent,
    )
    parts = (result.stdout.rstrip("\n").split(_SEP) + ["", "", "", ""])[:4]
    name, pkgver, pkgrel, pkgdesc = parts
    return {"name": name, "pkgver": pkgver, "pkgrel": pkgrel, "pkgdesc": pkgdesc}


def main():
    root = Path(__file__).parent
    packages = []

    for d in sorted(root.iterdir()):
        pkgbuild = d / "PKGBUILD"
        if not d.is_dir() or not pkgbuild.exists():
            continue
        meta = parse_pkgbuild(pkgbuild)
        if not meta["name"]:
            meta["name"] = d.name
        packages.append({
            "name":    meta["name"],
            "pkgver":  meta["pkgver"],
            "pkgrel":  meta["pkgrel"],
            "pkgdesc": meta["pkgdesc"],
            "subdir":  d.name,
            "git_url": REPO_URL,
        })

    out = root / "packages.json"
    out.write_text(json.dumps(packages, indent=2, ensure_ascii=False) + "\n")
    print(f"packages.json: {len(packages)} Pakete geschrieben.")


if __name__ == "__main__":
    main()
