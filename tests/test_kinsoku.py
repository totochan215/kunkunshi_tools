# -*- coding: utf-8 -*-
"""Tests du kinsoku (禁則処理 JLREQ) au repli des paroles ::lyrics.

Implémenté le 2026-11-20 (PR #42) : `_cap_lyr_column` ajuste le point de
coupe via `_kinsoku_adjust_cut` — 行頭禁則 avec追い出し, 行末禁則 pour les
ouvrantes. Scope : ::lyrics uniquement (seul le layout chindami coupe les
lignes de paroles au caractère ; vertical/mega ne repliquent qu'aux `|`
explicites, horizontal ne replie pas). Méta `@kinsoku simple|strict|off` +
CLI `--kinsoku` (défaut `simple`, `off` en nomura).

Usage :
    python3 tests/test_kinsoku.py
"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k


def cap(line, max_u, kinsoku="simple", indent=0):
    return k._cap_lyr_column([line], indent, max_u, kinsoku=kinsoku)


# 1. _kinsoku_adjust_cut en direct
assert k._kinsoku_adjust_cut("abc、d", 3, "simple") == 4   # 、 remonte (追い出し)
assert k._kinsoku_adjust_cut("abc、d", 3, "off") == 3      # off = coupe au caractère
assert k._kinsoku_adjust_cut("ab（cd", 3, "simple") == 2   # 行末禁則 : ouvrante passe après
assert k._kinsoku_adjust_cut("ab！cd", 2, "simple") == 2   # ！ autorisé en tête en simple
assert k._kinsoku_adjust_cut("ab！cd", 2, "strict") == 3   # ！ interdit en tête en strict
assert k._kinsoku_adjust_cut("abーcd", 2, "simple") == 3   # ー (cl-10) interdit en tête
print("OK _kinsoku_adjust_cut (行頭禁則/追い出し, 行末禁則, strict, off)")

# 2. 行頭禁則 : 、 ne démarre pas une sous-colonne (追い出し dans la précédente)
subs = cap("あいうえお、かき", 5, "simple")
assert subs[0][0][0] == "あいうえお、" and subs[1][0][0] == "かき", subs
subs_off = cap("あいうえお、かき", 5, "off")
assert subs_off[0][0][0] == "あいうえお" and subs_off[1][0][0] == "、かき", subs_off
print("OK 、 en追い出し (simple) vs coupe au caractère (off)")

# 3. 行末禁則 : une ouvrante ne termine pas une sous-colonne
subs = cap("あい（うえお", 3, "simple")
assert subs[0][0][0] == "あい" and subs[1][0][0].startswith("（"), subs
subs_off = cap("あい（うえお", 3, "off")
assert subs_off[0][0][0] == "あい（", subs_off
print("OK 行末禁則 （ passe à la sous-colonne suivante")

# 4. Petits kana (cl-11) interdits en tête
subs = cap("あきゃい", 2, "simple")
assert subs[0][0][0] == "あきゃ" and subs[1][0][0] == "い", subs
print("OK petit kana ゃ en追い出し")

# 5. Segment atomique ruby jamais coupé, même avec kinsoku actif
line = "あい〔安〕《やす》う"
subs = cap(line, 3, "simple")
joined = "".join(t for lines, _ind in subs for t in lines)
assert "〔安〕《やす》" in joined and subs[-1][0][0] == "う", subs
print("OK groupe ruby atomique intact au repli")

# 6. Méta @kinsoku reconnue ; valeur invalide -> AVERTISSEMENT + défaut
song = k.parse_kkml("@kinsoku strict\n::tab\n工 工\n::\n")
assert song.meta.get("kinsoku") == "strict"
err = io.StringIO()
with contextlib.redirect_stderr(err):
    k.render_svg(k.parse_kkml("@kinsoku bogus\n::tab\n工 工\n::\n"))
assert "AVERTISSEMENT" in err.getvalue(), err.getvalue()
print("OK @kinsoku en méta, AVERTISSEMENT sur valeur invalide")

# 7. E2E chindami : kinsoku actif change le repli (、 à la limite de colonne)
long_line = "あ" * 29 + "、" + "い" * 10   # 40 unités > max_lyr_u chindami (~29)
kkml_tmpl = "@layout chindami\n@kinsoku {k}\n::tab\n工 工 工 工\n::\n::lyrics\n{line}\n::\n"
err = io.StringIO()
with contextlib.redirect_stderr(err):
    svg_on = k.render_svg(k.parse_kkml(kkml_tmpl.format(k="simple", line=long_line)))[0]
    svg_off = k.render_svg(k.parse_kkml(kkml_tmpl.format(k="off", line=long_line)))[0]
assert "AVERTISSEMENT" not in err.getvalue(), err.getvalue()
assert svg_on != svg_off
print("OK e2e chindami : @kinsoku simple vs off produisent des repli différents")

# 8. CLI --kinsoku accepté
with tempfile.NamedTemporaryFile("w", suffix=".kkml", delete=False,
                                 encoding="utf-8") as f:
    f.write("@layout chindami\n::tab\n工 工\n::\n::lyrics\nあいう\n::\n")
    kkml_path = f.name
with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
    svg_path = f.name
r = subprocess.run([sys.executable, str(ROOT / "kkml2svg.py"), kkml_path,
                    "-l", "chindami", "--kinsoku", "strict", "-o", svg_path],
                   capture_output=True, text=True)
assert r.returncode == 0 and "AVERTISSEMENT" not in r.stderr, r.stderr
print("OK CLI --kinsoku strict (chindami, rc=0)")

print("\nTous les tests kinsoku passent.")
