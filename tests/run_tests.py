#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests d'échantillons homologues du dépôt kunkunshi_tools.

Convention d'homologie : des fichiers portant le même nom de base (sans
suffixe) à travers samples/kkml, samples/portama-json, samples/portama-pdf
et samples/svg sont des homologues — ils représentent la même chanson.

Normalisation des noms pour l'appariement :
- le suffixe de variante après « - » est conservé (ex. かぎやで風節-vocal
  reste distinct de かぎやで風節) ;
- les segments ruby entre crochets sont ignorés (国頭[くんじゃん]ジントヨー.pdf
  = 国頭ジントヨー.pdf), car certains exports Portama nomment les fichiers
  avec la lecture en ruby.

Usage :
    python3 tests/run_tests.py                 # rend chaque .kkml (v+h)
    python3 tests/run_tests.py --write-svg     # écrit en plus les rendus
                                                # dans samples/svg/
Le test échoue si kkml2svg retourne non-zéro ou émet un AVERTISSEMENT.
"""
import re
import sys
import argparse
import tempfile
import subprocess
from pathlib import Path

RUBY_RE = re.compile(r"\[[^]]*\]")
ROOT = Path(__file__).resolve().parent.parent
KKML2SVG = ROOT / "kkml2svg.py"
# Entrées pour l'appariement (samples/svg/ est une sortie, exclue)
DIRS = {
    "kkml": ROOT / "samples" / "kkml",
    "json": ROOT / "samples" / "portama-json",
    "pdf": ROOT / "samples" / "portama-pdf",
}
SVG_DIR = ROOT / "samples" / "svg"


def stem(path: Path) -> str:
    """Nom de base sans suffixe, segments ruby [...] retirés."""
    return RUBY_RE.sub("", path.stem)


def collect():
    """-> {stem: {kind: Path}}"""
    groups: dict = {}
    for kind, d in DIRS.items():
        if not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if p.name.startswith("."):
                continue
            groups.setdefault(stem(p), {}).setdefault(kind, p)
    return groups


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-svg", action="store_true",
                    help="écrire les rendus dans samples/svg/")
    args = ap.parse_args()

    groups = collect()
    failures = 0
    print(f"{len(groups)} homologue(s) détecté(s)\n")
    for st, kinds in sorted(groups.items()):
        parts = " ".join(f"{k}:{p.name}" for k, p in sorted(kinds.items()))
        print(f"== {st}  ({parts})")
        kkml = kinds.get("kkml")
        if kkml is None:
            print("   (pas de .kkml : ignoré pour le rendu)")
            continue
        for layout in ("vertical", "horizontal"):
            out = (SVG_DIR / f"{kkml.stem}-{layout}.svg"
                   if args.write_svg else None)
            with tempfile.NamedTemporaryFile(suffix=".svg") as tmp:
                r = subprocess.run(
                    [sys.executable, str(KKML2SVG), str(kkml),
                     "-l", layout, "-o",
                     str(out) if out else tmp.name],
                    capture_output=True, text=True)
            if r.returncode != 0 or "AVERTISSEMENT" in r.stderr:
                failures += 1
                print(f"   ECHEC {layout} : rc={r.returncode} "
                      f"{r.stderr.strip()}")
            else:
                print(f"   OK {layout}")
                if out:
                    print(f"   -> {out.relative_to(ROOT)}")
    print()
    if failures:
        print(f"{failures} échec(s)")
        return 1
    print("Tous les tests passent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
