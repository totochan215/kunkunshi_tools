"""Convention de nommage des SVG de tests/fixtures/synthetic/ (2026-11-25) :

    <nom du kkml>-<nom du layout>-<font>.svg        (1 page)
    <nom du kkml>-<nom du layout>-<font>-N.svg      (multi-page, N = n° de page)

avec <font> = valeur du @font_style du kkml (defaut mincho ; mincho|gothic|serif),
identique au 3e composant emis par `kkml2svg.py -l <layout> <kkml> -o <nom>.svg`.

Exception : les goldens obsoletes medley-samples-mega-p1/p2.svg sont conserves
tels quels (hors boucle de regeneration).
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SYN = ROOT / "tests" / "fixtures" / "synthetic"
LAYOUTS = ("vertical", "horizontal", "nomura", "chindami", "tuto", "mega")
FONTS = ("mincho", "gothic", "serif")
GOLDENS = {"medley-samples-mega-p1.svg", "medley-samples-mega-p2.svg"}


def font_of(kkml: Path) -> str:
    m = re.search(r"@font_style\s+(\w+)", kkml.read_text(encoding="utf-8"))
    return m.group(1) if m else "mincho"


def tracked_svgs():
    """SVG trackes par git (robuste aux artefacts non commites du repertoire).
    -z : pas de quoting core.quotepath sur les noms non-ASCII."""
    try:
        out = subprocess.run(["git", "ls-files", "-z", "--", str(SYN)],
                             cwd=ROOT, capture_output=True, check=True).stdout
        names = [Path(l).name for l in out.decode("utf-8").split("\0")
                 if l.endswith(".svg")]
        if names:
            return sorted(names)
    except Exception:
        pass
    return sorted(p.name for p in SYN.glob("*.svg"))


kkmls = {p.stem: font_of(p) for p in sorted(SYN.glob("*.kkml"))}
svgs = tracked_svgs()
assert svgs, "aucun SVG dans tests/fixtures/synthetic/"

# --- 1. Tout SVG tracke (hors goldens) suit <kkml>-<layout>-<font>[-N].svg ------
pat = re.compile(r"^(.+)-(" + "|".join(LAYOUTS) + r")-([a-z]+)(-\d+)?\.svg$")
n_ok = 0
for name in svgs:
    if name in GOLDENS:
        continue
    m = pat.match(name)
    assert m, f"nom non conforme: {name}"
    stem, layout, font, page = m.groups()
    assert stem in kkmls, f"{name}: aucun kkml {stem}.kkml dans le repertoire"
    assert font in FONTS, f"{name}: font inconnue {font!r}"
    assert font == kkmls[stem], \
        f"{name}: font {font!r} != @font_style de {stem}.kkml ({kkmls[stem]!r})"
    n_ok += 1
n_gold = len(GOLDENS & set(svgs))
print(f"OK 1. {n_ok} SVG conformes a <kkml>-<layout>-<font>[-N].svg "
      f"(+ {n_gold} goldens medley-samples-mega-p* conserves tels quels)")

# --- 2. Couverture : chaque kkml de test (hors medley-samples) a ses 6 layouts --
tested = [s for s in kkmls if s != "medley-samples"]
assert tested, "aucun kkml de test trouve"
for stem, font in kkmls.items():
    if stem == "medley-samples":
        continue
    for layout in LAYOUTS:
        n = sum(1 for s in svgs if s.startswith(f"{stem}-{layout}-{font}"))
        assert n >= 1, f"{stem}-{layout}-{font}*.svg manquant"
print(f"OK 2. {len(tested)} kkml de test x 6 layouts presents avec la bonne font")

# --- 3. La variante @font_style gothic porte bien le suffixe -gothic -----------
goth = [s for s, f in kkmls.items() if f == "gothic"]
assert goth, "aucune fixture @font_style gothic"
for stem in goth:
    assert any(s.startswith(f"{stem}-vertical-gothic") for s in svgs), stem
print(f"OK 3. variante gothic ({', '.join(s + '.kkml' for s in goth)}) nommee -gothic")

print("\nTous les tests de nommage des fixtures passent.")
