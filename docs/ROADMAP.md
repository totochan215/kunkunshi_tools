# Feuille de route — kunkunshi_tools

Dernière mise à jour : 25 septembre 2026

Pipeline : Portama JSON → KKML → SVG. Ce document est la référence unique pour
les priorités du projet. Statuts : ✅ fait · 🚧 en cours · ⬜ à faire · ❓ décision à trancher.

## 1. Validations en attente (bloquantes ou quasi)

- ⬜ Valider visuellement かぎやで風節 (KKML `songs/kagiya-defu.kkml`) contre le PDF :
  occurrences de `八` (U+E024, dan 5), silences `◯/尺♯` (dan 14), ornements `*` (dans 3, 10, 12, 18).
  Confirme le mapping PUA U+E024 = 八.
- ⬜ Régénérer et valider le SVG de test des souhou (uchi-utu `*`, kaki-utu `^`, aki-utu `v`,
  kachi-utu `<`, kuubanchi `s`, taachi `=`) ; ajuster dx/dy/scale/rotate selon retours visuels.
- ⬜ Valider le rendu vocal multi-caractères (うちなぐち) : empilement petits kana, ー vertical,
  chevauchement bord inférieur. Support vocal en mode horizontal non implémenté (priorité verticale).
- ⬜ Valider visuellement les accords (`四-五`, `+`) et le rendu condensé イ下尺 / ロ下尺 sans cercle.

## 2. Phases fonctionnelles (séquencement P0 → P4)

### P0 — Référence 野村流 dans la documentation — ⬜
- Section « Référence 野村流 » dans `docs/notation.md` : modèle à 4 positions/case,
  inventaires techniques instrumentales et vocales, code couleur rouge (haut) / noir (bas).
- Enrichir les positions vocales : 才 凡 勺.
- Table d'alias de normalisation des tokens.
- Relecture des scans sources pour la fidélité des formes (pré requis de P3).

### P1 — Techniques instrumentales étendues — 🚧
- ✅ Position 下八 (kandokoro propre, octave de 中) — commit `8b4d683`.
- ⬜ Suffixes techniques supplémentaires dans `TECHNIQUE_SUFFIXES` : 打抜音, 抑下し, 開音, 掻音,
  小字 (~70 %). Patron rodé, effort faible.
- Non couvert volontairement : イ下八 / ロ下八 (non attestés, repli dégradé).

### P2 — Spécification du bloc positionné `::ruby` — ❓ décision structurante
- DÉCISION À TRANCHER : grille `::ruby` sur 4 positions/case
  (拍子 / 二分五厘 / 五分 / 七分五厘) plutôt que les 3 unités Portama.
- Import Portama : mapping 3 → 4 le plus proche.
- `::vocal` (alignement strict syllabe ↔ note) reste le modèle d'écriture simple ;
  incompatible avec 聲楽譜 ; le bloc positionné est le substrat commun.
- Goulot d'étranglement : à trancher avant P3.
- Constantes mesurées disponibles (かぎやで風節, PDF vectoriel) : ruby fs = 0,65 × note fs,
  avance ligne = cell_h/3, tuck petit kana +1,18 × fs, offset x +0,1 × fs.
- ⬜ Mesurer le rendu du chōonpu ー si un PDF ruby avec voyelles longues est disponible.

### P3 — Bloc 聲楽譜 (notation vocale) — ⬜ (dépend de P0 et P2)
- Bloc pairé à `::tab`, grammaire type `発声法:hauteur[:上|平|下]`.
- Table de rendu des ~20 発声法記号 (上吟/下吟/次第上/次第下/押切/直吟/呑み/掛/大掛/当/
  ネーキ/クダミ/ユルシ/振い/廻い/振上げ/内グヰ/突吟/スクヰ…).
- Rendu : glyphes Unicode (▲○●□↑) ou formes SVG dessinées ; rouge/noir via `fill` SVG.
- 勺 凡 才 acceptés comme hauteurs ; 声だし / 声切り en colonne marker.

### P4 — Annotations de marge et de tempo — ⬜
- 指位記号 (doigtés) : numéraux encerclés ㊀㊁㊂㊃ (野村流), colonne/marge dédiée,
  jamais dans la grille (collision avec la normalisation REST_VARIANTS → ◯).
- 撥記号 (coups de plectre).
- Annotations de tempo : 五分拍子 (「此間X分Y厘脉」), 少緩弾 / 少早弾.

## 3. Backlog Portama (conversion JSON → KKML)

- ⬜ Compléter le mapping des ornements (`orn` au-delà de `"u"`).
- ⬜ Comprendre les champs `chogen` (4 vs 5), `rhythm`, `rhythmMode`.
- ⬜ Recenser les autres accordages (`choshi` : ni, san…) et leur mapping PUA.
- ⬜ Round-trip Portama : variante « raw » de `::ruby` (ligne allRubyData littérale, sans perte).
- ⬜ Contrepartie `::vocal` : règle note = floor(unités/3), validée sans collision sur かぎやで風節.

## 4. Long terme

- ⬜ Conversion KKML -> Portama JSON
- ⬜ Pipeline de publication LaTeX : collaboration avec éditeurs et communauté large.
  Pas de LilyPond / portée standard.
- ⬜ GUI : combler l'écart avec Portama (avantage GUI).

## 5. Positionnement

Le convertisseur est plus avancé que threedaymonk/kunkunshi et Kunkunshi Editor
(accords, positions composées, souhou, vocal, répétitions). Portama reste en avance
sur l'interface. La priorité est la fidélité notationnelle (P0 → P3) avant la
publication (LaTeX) et l'ergonomie (GUI).
