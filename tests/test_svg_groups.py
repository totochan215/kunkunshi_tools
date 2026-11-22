# -*- coding: utf-8 -*-
"""Tests : chaque flèche/symbole de répétition est un groupe SVG <g>.

Implémenté le 2026-11-21 : `_render_repeat_arrow`, `_h_repeat_arrow`
(class="repeat-arrow") et `_render_vrep_marker`, `_h_vrep_marker`
(class="vocal-rep") émettent un seul <g> par marqueur, avec fill/stroke/
stroke-width sur le <g> (hérités par le path + la pointe).

Usage :
    python3 tests/test_svg_groups.py
"""
import contextlib
import io
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import kkml2svg as k

KKML = "::tab\n|: 合 工 :| (: 尾 :)\n::\n"  # 1 boucle |: :| + 1 boucle vocale (: :)

for layout in ("vertical", "horizontal"):
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        svg = "".join(k.render_svg(k.parse_kkml(KKML), layout=layout))
    assert "WARNING" not in err.getvalue(), err.getvalue()
    ET.fromstring(svg)  # XML bien formé
    assert svg.count('<g class="repeat-arrow"') == 2, svg.count('<g class="repeat-arrow"')
    assert svg.count('<g class="vocal-rep"') == 2
    assert svg.count("</g>") == 4
    # chaque <g> porte le trait et englobe exactement path + pointe (polygon/circle)
    root = ET.fromstring(svg)
    ns = "{http://www.w3.org/2000/svg}"
    groups = [e for e in root.iter(ns + "g")]
    assert len(groups) == 4
    for g in groups:
        assert g.get("fill") == "none" and g.get("stroke") and g.get("stroke-width")
        kids = list(g)
        assert len(kids) == 2 and kids[0].tag == ns + "path"
        assert kids[1].tag in (ns + "polygon", ns + "circle")
        for kid in kids:  # plus d'attribut de trait sur les enfants (hérité du <g>)
            assert "stroke" not in kid.attrib and "fill" not in kid.attrib
    print(f"OK {layout} : 2 <g class=\"repeat-arrow\"> + 2 <g class=\"vocal-rep\">, XML valide")

print("\nTous les tests de groupes SVG passent.")
