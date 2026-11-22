# -*- coding: utf-8 -*-
"""Tests du codage des doigtés (yubii) en KKML.

Encodage retenu (2026-11-19) : le doigté est un SUFFIXE de note dans `::tab`,
㊀-㊃ (U+3280-U+3283) accolés au token (ex. 合㊀), jamais une position autonome
(confusion avec le silence ◯). Variantes parenthésées ㈠-㈣ (U+3220-U+3223)
normalisées en ㊀-㊃. Portama : champ cell.yubii 1-4 (PUA U+E041-E044).
Rendu SVG calibré sur le PDF Portama (テスト節.pdf) : glyphe à gauche de la
note, même baseline, fs ≈ 0,735 × fs note.

Usage :
    python3 tests/test_yubii.py
"""
import contextlib
import io
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k
import portama2kkml as p2k

Y = {1: chr(0x3280), 2: chr(0x3281), 3: chr(0x3282), 4: chr(0x3283)}
GO, GOU = chr(0x5408), chr(0x4e94)          # 合 五
UCHI = chr(0xFF40)                           # ＠ rendu de uchi-utu
PAREN1 = chr(0x3220)                         # ㈠ variante parenthésée de ㊀
REST = chr(0x25EF)                           # ◯ silence


def render(kkml):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svgs = k.render_svg(k.parse_kkml(kkml))
    return svgs, err.getvalue()


# 1. ㊀-㊃ ne sont pas des positions de grille
assert not (k.YUBII_CHARS & k.POSITION_CHARS)
assert k.YUBII_CHARS <= k.TECHNIQUE_CHARS  # strippés comme les autres suffixes
print("OK ㊀-㊃ absents de POSITION_CHARS, présents dans TECHNIQUE_CHARS")

# 2. Suffixe yubii rendu (glyphe ㊀ dans le SVG, taille réduite, pas d'alerte)
svgs, err = render(f"::tab\n{GO}{Y[1]} {GOU}\n::\n")
assert Y[1] in svgs[0] and "WARNING" not in err, err
import re
m = re.search(r'<text x="([\d.]+)"[^>]*font-size="(\d+)"[^>]*>' + Y[1], svgs[0])
assert m, "pas de glyphe ㊀"
mn = re.search(r'<text x="([\d.]+)"[^>]*font-size="(\d+)"[^>]*>' + GO, svgs[0])
assert mn
yb_x, yb_fs = float(m.group(1)), int(m.group(2))
note_x, note_fs = float(mn.group(1)), int(mn.group(2))
# calibrage Portama : à gauche de la note (dx ≈ 0,91 × note_fs), fs ≈ 73 %
assert abs((note_x - yb_x) - 0.91 * note_fs) < 0.5, (note_x, yb_x)
assert abs(yb_fs / note_fs - 0.735) < 0.1, (yb_fs, note_fs)
print(f"OK {GO}㊀ rendu à gauche de la note (dx={note_x-yb_x:.2f}, fs={yb_fs}/{note_fs})")

# 3. Combinaison avec un suffixe de technique
svgs, err = render(f"::tab\n{GO}'{Y[2]}\n::\n")
assert Y[2] in svgs[0] and UCHI in svgs[0] and "WARNING" not in err, err
print(f"OK {GO}'㊁ : technique + yubii rendus ensemble")

# 4. ㊀ seul : avertissement, jamais rendu comme une note
svgs, err = render(f"::tab\n{Y[1]} {GO}\n::\n")
assert "WARNING" in err and "yubii" in err, err
print("OK ㊀ seul : avertissement « yubii sans note », rien rendu comme note")

# 5. Variantes parenthésées normalisées (idempotent)
tok, changed = k._normalize_tab_token(GO + PAREN1)
assert tok == GO + Y[1] and changed, tok
tok2, changed2 = k._normalize_tab_token(GO + Y[1])
assert tok2 == GO + Y[1] and not changed2
print("OK ㈠ -> ㊀ (normalisation canonique, idempotente)")

# 6. Croche et shuffle avec yubii en fin de token
for t in (f"{GO}/{GOU}{Y[1]}", f"{GO}:{GOU}{Y[2]}"):
    svgs, err = render(f"::tab\n{t}\n::\n")
    assert t[-1] in svgs[0] and "WARNING" not in err, (t, err)
print(f"OK croche {GO}/{GOU}㊀ et shuffle {GO}:{GOU}㊁")

# 7. portama2kkml : cell.yubii -> suffixe ; note PUA E041-E044 -> suffixe
tok, yb = p2k.cell_to_note({"note": chr(0xE000), "yubii": 1}, True)
assert tok == GO and yb == Y[1], (tok, yb)
tok, yb = p2k.cell_to_note({"note": chr(0xE043)}, True)
assert tok is None and yb == Y[3], (tok, yb)
dans = p2k.dan_to_tokens([{"note": chr(0xE000), "yubii": 4}, {"note": ""},
                          {"note": chr(0xE010)}, {"note": ""}])
assert dans[0] == GO + Y[4], dans
print("OK portama2kkml : yubii=4 -> 合㊃, PUA E043 -> ㊂ sans note")

# 8. portama2kkml sur l'échantillon qui contient des yubii (テスト節.json :
#    dan 2, cellules 18/20/22 -> 合㊀ 合㊁ 合㊃). Localisation via le JSON :
#    os.listdir n'a pas d'ordre garanti (テンヨー節 commence aussi par テ).
import json as _json
target = None
for n in sorted(os.listdir("samples/portama-json")):
    j = _json.load(open(f"samples/portama-json/{n}", encoding="utf-8"))
    hits = [(di, c["yubii"]) for di, dan in enumerate(j.get("score", []))
            for c in dan if c.get("yubii")]
    if hits:
        target = (n, hits)
assert target, "aucun échantillon Portama avec yubii"
fn, hits = target
r = subprocess.run([sys.executable, "portama2kkml.py",
                    f"samples/portama-json/{fn}"],
                   capture_output=True, text=True)
assert r.returncode == 0, r.stderr
tab_lines = [ln for ln in r.stdout.split("::tab")[1].splitlines() if ln.strip()]
for di, yb in hits:
    assert di < len(tab_lines), (di, len(tab_lines))
    assert GO + Y[yb] in tab_lines[di], (fn, di, tab_lines[di])
n_yb = sum(ln.count(y) for ln in tab_lines for y in Y.values())
assert n_yb == len(hits), (n_yb, len(hits))
print(f"OK {fn} -> {len(hits)} doigtés convertis (ex. dan {hits[0][0]} : {GO}{Y[hits[0][1]]})")

# 9. Extraction inverse (préparation kkml2portama) : suffixe final -> int yubii
SUFFIX_TO_INT = {v: i for i, v in Y.items()}
for t in (f"{GO}{Y[1]}", f"{GO}/{GOU}'{Y[3]}", f"-{Y[2]}"):
    yb_tok, rest = None, t
    while rest and rest[-1] in k.YUBII_CHARS:
        yb_tok, rest = rest[-1], rest[:-1]
    assert yb_tok and SUFFIX_TO_INT[yb_tok] in (1, 2, 3, 4)
print("OK extraction du suffixe ㊀-㊃ en fin de token (sens Portama)")

# 10. Non-régression : portama2kkml -> kkml2svg sur les 7 échantillons réels
#     (テスト節 exclu : PUA composites non mappés, '?' pré-existant)
for n in sorted(os.listdir("samples/portama-json")):
    if n.startswith(chr(0x30C6)):
        continue
    r = subprocess.run([sys.executable, "portama2kkml.py",
                        f"samples/portama-json/{n}"], capture_output=True, text=True)
    assert r.returncode == 0, (n, r.stderr)
    svgs, err = render(r.stdout)
    assert "WARNING" not in err, (n, err)
print("OK non-régression : 7 échantillons Portama -> KKML -> SVG sans avertissement")

print("Tous les tests yubii passent.")
