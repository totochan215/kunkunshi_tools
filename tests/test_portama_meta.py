# -*- coding: utf-8 -*-
"""Tests des métadonnées de compatibilité Portama en KKML.

@musicno / @chogen / @speed / @rythm / @rythm_mode (doc : docs/kkml-format.md)
sont stockées telles quelles (chaînes) dans song.meta et mappées vers les
champs JSON Portama musicno (int) / chogen / speed / rhythm / rhythmMode,
pour permettre le round-trip Portama -> KKML -> Portama.

Usage :
    python3 tests/test_portama_meta.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k
import portama2kkml as p2k

FIELDS = ("musicno", "chogen", "speed", "rhythm", "rhythmMode")

# 1. Round-trip des 5 champs sur tous les échantillons Portama
for fn in sorted(os.listdir("samples/portama-json")):
    j = json.load(open(f"samples/portama-json/{fn}", encoding="utf-8"))
    kkml = p2k.convert_portama_to_kkml(j)
    meta = k.parse_kkml(kkml).meta
    back = p2k.portama_fields_from_meta(meta)
    expect = {f: j[f] for f in FIELDS if f in j}
    assert back == expect, (fn, back, expect)
    # émission verbatim dans le KKML (ordre canonique du cleaner : après @marker)
    for key, field in p2k.META_TO_PORTAMA_FIELD.items():
        if field in j and j[field] not in (None, ""):
            assert f"@{key} {j[field]}" in kkml, (fn, key)
print(f"OK round-trip @musicno/@chogen/@speed/@rythm/@rythm_mode sur "
      f"{len(os.listdir('samples/portama-json'))} échantillons (valeurs et types exacts)")

# 2. Tolérance @cléValeur collé (ces clés sont dans META_KEYS)
song = k.parse_kkml("@musicno5172\n@chogen5\n@speed100\n@rythm0\n@rythm_mode0\n::tab\n合\n::\n")
assert song.meta["musicno"] == "5172", song.meta
assert song.meta["chogen"] == "5", song.meta
assert song.meta["speed"] == "100", song.meta
assert song.meta["rythm"] == "0", song.meta
assert song.meta["rythm_mode"] == "0", song.meta
print("OK formes collées @musicno5172 etc. reconnues (META_KEYS)")

# 3. Absence préservée : JSON sans ces champs -> pas de méta -> pas de champ
mini = {"title": "t", "choshi": "hon", "score": [[{"note": ""}]]}
kkml = p2k.convert_portama_to_kkml(mini)
assert not any(f"@{key} " in kkml for key in p2k.META_TO_PORTAMA_FIELD), kkml
assert p2k.portama_fields_from_meta(k.parse_kkml(kkml).meta) == {}
print("OK absence des champs préservée (pas de méta émise, pas de champ reconstruit)")

# 4. musicno reste utilisé par le rendu chindami (n° > 999 tronqué mod 1000)
svg = k.render_svg(k.parse_kkml("@layout chindami\n@musicno 5168\n::tab\n合\n::\n"),
                   layout="chindami")[0]
assert "168" in svg and "5168" not in svg
print("OK chindami : @musicno 5168 rendu '168' (mod 1000, non-régression)")

# 5. Le cleaner préserve ces métas (ordre canonique, idempotent)
with open("samples/portama-json/安波節.json", encoding="utf-8") as f:
    j = json.load(f)
kkml = p2k.convert_portama_to_kkml(j)
import tempfile
with tempfile.NamedTemporaryFile("w", suffix=".kkml", delete=False,
                                 encoding="utf-8") as f:
    f.write(kkml)
    path = f.name
r = subprocess.run([sys.executable, "kkml_cleaner.py", "-n", path],
                   capture_output=True, text=True)
os.unlink(path)
assert r.returncode == 0, r.stderr
out = r.stdout
for key, field in p2k.META_TO_PORTAMA_FIELD.items():
    if field in j:
        assert f"@{key} {j[field]}" in out, (key, out)
# idempotence : cleaner(cleaner(x)) == cleaner(x)
with tempfile.NamedTemporaryFile("w", suffix=".kkml", delete=False,
                                 encoding="utf-8") as f:
    f.write(out)
    path2 = f.name
r2 = subprocess.run([sys.executable, "kkml_cleaner.py", "-n", path2],
                    capture_output=True, text=True)
os.unlink(path2)
assert r2.stdout == out
print("OK cleaner : métas Portama conservées, ordre canonique, idempotent")

print("Tous les tests portama_meta passent.")
