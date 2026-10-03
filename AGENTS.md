# AGENTS.md — contexte agent pour kunkunshi_tools

Ce fichier contient la connaissance **machine/projet** destinée aux agents IA (et contributeurs techniques) : roadmap, statuts, points ouverts, mesures de calibrage, architecture du code. La documentation **humaine** (notation musicale, formats, layout) est dans `docs/` et le README — ne pas y mélanger de suivi de tâches.

Règles :
- Tout ajout de statut, TODO, mesure ou point ouvert va ici, jamais dans `docs/`.
- `docs/` reste la référence du format KKML et de la notation ; le code est la source de vérité du comportement.
- Tests : `python3 tests/run_tests.py`. Python 3 stdlib uniquement, aucune dépendance.

---
# Feuille de route — kunkunshi_tools

Dernière mise à jour : 25 septembre 2026

Pipeline : Portama JSON → KKML → SVG. Ce document est la référence unique pour
les priorités du projet. Statuts : ✅ fait · 🚧 en cours · ⬜ à faire · ❓ décision à trancher.

## 1. Validations en attente (bloquantes ou quasi)

- ⬜ Valider visuellement かぎやで風節 (KKML `samples/kkml/かぎやで風節.kkml`) contre le PDF :
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

# Architecture des convertisseurs Python

> Contenu déplacé depuis `docs/converter-architecture.md`. Documentation agent : structure interne du code, pour la navigation lors des modifications. La documentation utilisateur reste dans `docs/`.

## `kkml2svg.py`

Python 3 autonome, ~2096 lignes. Ce dépôt est la source de vérité du code.

### CLI

```bash
python3 kkml2svg.py chanson.kkml -o chanson.svg
python3 kkml2svg.py chanson.kkml            # -> chanson.svg
cat chanson.kkml | python3 kkml2svg.py -     # stdin -> stdout
```

Options : `-o output`, `-c cols`, `-l vertical|horizontal`

### Structure du code

### 0. Rendu multipage (`render_svg`)

- `render_svg(...)` retourne désormais une **liste de SVG** (un par page).
- Pagination : `@page_dans N` (méta) ou `-p/--page-dans N` (CLI). Défaut : None = une seule page (comportement historique).
- `_render_vertical` découpe les sections tab/tab-lyrics en pages de N dans ; les colonnes vocales (`vocal_data`) sont tranchées en synchronisation avec les colonnes de tab (même slice).
- Sections lyrics et titre vertical : répétés sur chaque page.
- `main()` : 1 page → sortie simple ; n pages → `stem-1.svg` … `stem-n.svg`.

### 1. Parseur KKML (`parse_kkml`, lignes ~129-210)

- Classes `Song` (meta, blocks, cols, layout) et `Block` (kind, label, lines)
- Lit ligne par ligne : commentaires `#`, métadonnées `@`, blocs `::kind`, fermeture `::`
- Blocs supportés : `tab`, `lyrics`, `tab-lyrics`, `vocal`, `section`
- `::vocal` se paire au bloc `::tab` précédent : chaque ligne vocale est aplatie avec padding par ligne (`-`) sur la structure de la ligne de tab de même index ; l'excédent est tronqué. La syllabe i reste alignée sur la note i.

#### 2. Rendu SVG (`render_svg`, ~212-308)

- Regroupe les blocs en sections 4-uplets `(section_title, content, kind, vocal_data)`
- `has_vocal = any(s[3] or s[2] == "vocal")` → active automatiquement la colonne marker
- Constantes de rendu vocal : `SYLLABLE_FS = min(int(cell_h * 0.35), int(marker_w * 0.8))`
- Route vers `_render_vertical` ou `_render_horizontal`

#### 3a. Rendu vertical (`_render_vertical`, ~309-580)

- Offsets `title_offset`, `lyrics_offset`, `marker_w = cell_w // 2` si marker
- Helpers : `_wrap_vertical` (découpage en colonnes de N), `_split_verses` (couplets)
- Titre vertical à droite, paroles verticales à gauche

#### 3b. Rendu vocal (`_draw_vertical_vocal`, ~613 + `SMALL_KANA`)

- Un token = une syllabe, rendu dans la colonne marker centré sur la note
- Token multi-caractères empilé : caractère principal aligné sur la note, caractères combinants dessous (espacement `syllable_fs * 0.85`), ー pivoté 90°
- Chevauchement du bord inférieur de case accepté

#### 3c-nomura. Rendu Nomura-ryu (`_render_nomura`)
- Layout `nomura` (`@layout nomura` / `-l nomura`) : page A4 portrait 595,28 × 841,89 pt, cadre filet, 12 cases/dan, marker = largeur d'une case à DROITE des notes (filets vertical ×2 + haut/bas), jusqu'à 7 dans/page, titre = 1 dan complet en colonne droite p.1, paroles en colonnes verticales, multipage automatique (1 SVG/page). `@marker on` forcé (cosubstantiel).
- **3 constantes primaires** (tout le reste est dérivé) : `NOMURA_FRAME_W = 559,3` (largeur cadre, médiane 12 pages), `NOMURA_FRAME_H = 745,9` (hauteur cadre), `NOMURA_DAN_GAP = 14,5` (marge de dans M unique). Dérivés : `FRAME_MARGIN_X = (595,28 − 559,3)/2 ≈ 18` ; `FRAME_MARGIN = (841,89 − 745,9)/2 ≈ 48` ; `CELL_W = (FRAME_W − 8M)/14 ≈ 31,7` ; `CELL_H = (FRAME_H − 2M)/12 ≈ 59,7` ; `group_w = 2×CELL_W`.
- **Marge M unique partout** : haut cadre→grille, droite cadre→1er dan (marker), entre dans, gauche 7e dan→gauche cadre, bas grille→bas cadre. Géométrie : `grid_y0 = frame_y0 + M` ; `x_right = frame_x1 − M` ; chaque dan décrémente `x_right −= (group_w + M)`. Vérifié : boucle au pt près.
- Titre : centré exactement entre le filet droit de la première colonne marker et le filet droit de page (`tx = x_right − group_w/2`) ; taille `cell_h × 0,43` ; indentation `cell_h × 1,8` sous le haut de grille.
- Couplets (`::lyrics`, préfixés ⚪︎, `||` = saut sans colonne blanche) : **3 colonnes max par dan virtuel** calées pile sur la largeur d'un dan (`LYRICS_COL_W = group_w/3`) ; au-delà de 3 colonnes → dan virtuel supplémentaire espacé de M.
- **Pagination couplets** : la musique remplit les pages normalement (p.1 = 7 − 1 si titre, puis 7 dans ; jamais réduite, jamais de dan de musique perdu). Les couplets occupent les dans LIBRES de la dernière page de musique ; l'excédent de dans virtuels passe sur des pages suivantes dédiées couplets (7 dans virtuels max/page). **Jamais de débordement du cadre.** Tuple de page : `(cols, vocal_cols, is_last, lyr_dans_here, lyr_col_offset)`.
- Aplatit les sections tab en flux de colonnes de 12 ; `tab-lyrics` → notes + syllabes dans le marker. Sélecteurs de variante (U+FE00–FE0F) non rendus (éviter l'« espace doublée » en tête de couplet).

#### 3c. Rendu horizontal (`_render_horizontal`, ~794)

- Mode songbook : gauche→droite, haut→bas. Vocal horizontal non implémenté (priorité au vertical)

#### Fonctions de dessin

- `_draw_vertical_tab` — grille verticale, deux passes (rectangles puis notes) ; rend aussi les données vocales pairées
- `_draw_vertical_tab_lyrics` — grille + positions (haut) + syllabes (bas)
- `render_cell` (~1147) — rend un token (voir ci-dessous)
- `_note_svg` — rendu d'une note unique
- `_render_techniques` — souhou autour de la cellule ; suffixes avec `dx/dy/scale/rotate` individuels, paramètre `text_w` pour multi-caractères
- `_strip_repeat_marks` + `_render_repeat_arrow` — marques `|:`/`:|` détachées des tokens, flèches ↓/↑ rendues dans la colonne marker
- `_render_end_circle` — cercle de fin
- `_render_vertical_ruby` / `_render_vertical_text` / `_render_horizontal_ruby` / `_render_horizontal_text` — texte vertical/horizontal (titres, paroles, ruby)

#### Tokens gérés par `render_cell` (ordre de traitement)

1. Marques de répétition détachées avant traitement (`_strip_repeat_marks`)
2. Cas spéciaux : EMPTY (`-`), SUSTAIN (`.` → ・), REST (◯/variants)
3. Suffixes de technique extraits de la fin du token
4. 尺♯ selon `@shaku_sharp` (jamais entouré)
5. Accords `A-B` / `A-B-C` (séparateur `-`, max 3 notes) : notes empilées à 72%
6. 下老 et positions hautes `イX`/`ロX` : un seul `<text>` avec `textLength` + `lengthAdjust="spacingAndGlyphs"` (下老 demi-largeur, positions hautes 120%)
7. イ下尺 : 3 caractères condensés (イ下尺), textLength 180%, sans cercle
8. Croche `A/B` (note principale + à cheval), shuffle `A:B` (deux notes empilées)
9. Note simple centrée ; ornement multi-caractères empilé

#### Constantes notables

- `POSITION_CHARS`, `REST_VARIANTS`, `TECHNIQUE_SUFFIXES` (uchi-utu `*`, kaki-utu `^`, aki-utu `v`, kachi-utu `<`, kuubanchi `s`, taachi `=`)
- `HIGH_PREFIX_I` / `HIGH_PREFIX_RO` (positions hautes イ/ロ + kanji compatibles)
- `FONT_STYLES` : serif (défaut), mincho, gothic (`@font_style`)
- `VERSE_*` : regex de numéros de couplet, puces, genre (男/女)

### Paramètres par défaut

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| cell_w | 52 | largeur de case |
| cell_h | 58 | hauteur de case |
| font_size | 22 | taille police notes |
| cols | 12 | lignes par colonne (vertical) — défaut depuis le 14 sept. 2026 (avant : 9) |
| marker_w | cell_w // 2 | colonne marker (auto si ::vocal) |

## `portama2kkml.py`

Python 3 autonome. Ce dépôt est la source de vérité du code.

- Mapping PUA → kanji (voir [format Portama](docs/portama-format.md))
- Paires (main, straddle) → noires, croches (A/B) ou shuffles (A:B) selon `isSmall`
- `acc: "sharp"` → 尺♯, `orn: "u"` → suffixe `*`
- `repeatStart/repeatEnd` → `|:` / `:|`
- `choshi` → `@tuning`, `cellsPerDan / 2` → `@cols`
- N'exporte pas encore `allRubyData` (proposition `::ruby` / conversion `::vocal`, voir `docs/kkml-format.md`)

## Séparation documentation humaine / agent

- `AGENTS.md` (racine) : contexte agent — roadmap, priorités, points ouverts, mesures, architecture du code. Ne pas déplacer vers `docs/`.
- `docs/` : documentation humaine uniquement (notation musicale, formats KKML et Portama, layout SVG). Ne pas y ajouter de statuts de tâche, TODO, mesures de calibrage ou références de commits.
- Mettre à jour la section « Validations en attente » et les statuts de phase lors de chaque changement fonctionnel.


## Détails de rendu (fonction render_cell) — déplacés depuis docs/notation.md

- Noire : `font-size = fs` (ou `int(fs*0.67)` si kuubanchi), `y = cy + 7`, `text-anchor = middle`
- Croche, note principale : `font-size = effective_fs`, `y = cy + 7`
- Croche, note à cheval : `font-size = int(effective_fs * 0.713)` (+15%), position `straddle_y` calculée sur `fs` de base (inchangée par `s`), `y = straddle_y`
- Shuffle, note supérieure : `font-size = int(effective_fs * 0.72)`, `y = cy - fs * 0.18 + sh_pos/3` (position sur fs de base)
- Shuffle, note inférieure : `font-size = int(effective_fs * 0.72)`, `y = cy + fs * 0.42 + sh_pos/3` (position sur fs de base)
- 尺 entouré (noire) : cercle SVG `r = effective_fs * 0.6325` (+15%), centre `(cx, cy+2)`, `stroke-width=1`
- 尺 entouré (croche, note principale) : même cercle que la noire, dessiné avant le texte
- 尺 entouré (croche, note à cheval) : cercle `r = ss * 0.713` (+15%), centre décalé vers le bas
- Marques diacritiques : police serif, `font-size = int(effective_fs * 1.1)` (+10%). Positionnement : voir les deux modes ci-dessus (notes simples vs tokens multi-caractères avec text_w)
- uchi-utu : caractère ｀ (accent grave, U+FF40) en haut-droite
- 下老 : un seul `<text>` avec `textLength = effective_fs * 1.0`, `lengthAdjust="spacingAndGlyphs"`, `text-anchor` non spécifié (left). Techniques passées avec `text_w=effective_fs * 1.0`
- Positions hautes (イ尺, イ五, etc.) : un seul `<text>` avec `textLength = effective_fs * 1.2`, `lengthAdjust="spacingAndGlyphs"`. Techniques passées avec `text_w=effective_fs * 1.2`
- fs (font_size) par défaut = 22, cell_w = 52, cell_h = 58

## Offsets des marques diacritiques (TECHNIQUE_SUFFIXES) — déplacés depuis docs/notation.md

Les marques diacritiques (`*`, `^`, `v`, `<`) sont rendues dans la même police et la même taille que la note (`int(fs * 1.1)`, +10%). Règle de positionnement : l'encre visible du signe ne doit pas chevaucher l'encre visible de la note. Chaque signe a ses propres offsets (dx, dy) dans `TECHNIQUE_SUFFIXES` :

- uchi-utu (｀) : `dx=0.22`, `dy=0.05` (en haut-droite)
- kaki-utu (┗ roté 180°, échelle 0.75) : `dx=0.28`, `dy=-0.22` (en haut-droite, barre supérieure au-dessus de la note)
- aki-utu (V) : `dx=0.45`, `dy=0.15` (en bas-gauche)
- kachi-utu (┗) : `dx=0.45`, `dy=0.15` (en bas-gauche)

Les offsets sont des multiplicateurs de `fs` : `tx = cx ± fs * dx`, `ty = cy + 7 + fs * dy`. Aucun souhou ne modifie les coordonnées de la note, sauf `s` qui réduit la taille à 67% sans déplacer le centre.

## Positionnement des syllabes vocales — déplacé depuis docs/notation.md

- Taille de police : SYLLABLE_FS = min(int(cell_h * 0.35), int(marker_w * 0.8)) ≈ 20px avec les valeurs par défaut (cell_w=52, cell_h=58, marker_w=26)
- Position x : centre de la colonne marker = `x + cell_w + marker_w / 2`
- Position y : `cy + cell_h / 2 + syllable_fs / 3` (centré verticalement sur la note)
- Couleur : gris foncé (#333)
- Police : serif (même que les notes)


## Sections de `docs/portama-format.md` à documenter (TODO déplacés)

- Structure du tableau `allRubyData` : 1 array par page, 1 ligne par dan, 3 unités double largeur par cellule. Description détaillée à documenter.
- Structure du tableau `allLyricsData` : `id`, `content`, `x`, `y`, `width`, `height`, `fontSize` — description détaillée à documenter.
- Mapping conversion restant à définir : `yubii: 1-4` → KKML, `vocalPosMarkers` → KKML, orn `nu` → suffixe `n` (proposition).
- `choshi` + `chogen` → `@tuning` (chogen − 5 = demi-tons ; pas encore implémenté).
- Point ouvert : `repeatStart`/`repeatEnd`/`vocalRepStart`/`vocalRepEnd` ne rendent RIEN dans テスト節.pdf (dan 1, cases 13–19 : aucun graphique ni flèche), alors que d'autres pièces rendent des flèches dans la colonne marker. Le déclencheur exact du rendu des flèches reste à élucider.
- `kkml2pdf.py` : script non écrit. Pipeline KKML → PDF à définir.
- ✅ SVG multipage (2026-10-02) : `@page_dans` / `-p` implémentés dans kkml2svg.py ; contrainte Portama 12 dans/page vérifiée sur かぎやで風節.pdf. Suite : modèles de page (Portama A4 paysage fait implicitement ; Nomura-ryu portrait, chindami, Paris Sanshin Club en attente d'exemples à téléverser), puis assemblage PDF (embed polices CJK).
✅ Layout Nomura-ryu (2026-10-03) : page A4 portrait, filet de cadre, 12 cases/dan, 7 dans/page, titre p.1, paroles dernière page — mesuré sur samples/nomura-ryu-pdf, premier test sur かぎやで風節 (3 pages).
✅ Géométrie Nomura (2026-10-03) : 3 constantes primaires (cadre 559,3 × 745,9 pt, marge de dans M = 14,5 unique partout), tout dérivé — boucle vérifiée au pt près (commits e288f91…).
✅ Couplets nomura (2026-10-03) : 3 colonnes/dan virtuel calées sur la largeur de dan (eebf527, 1bbf95c) ; excédent sur pages suivantes dédiées, jamais de débordement du cadre, jamais de dan de musique perdu (3ec6aca). Validé sur cas limite 6 couplets (4 pages, p.4 couplets seuls).

## Constantes de calibrage mesurées sur les PDF Portama (recherche)

**Pagination vérifiée (かぎやで風節.pdf, 2 pages)** : maximum 12 piles (dans) par page — page 1 = 12 séparateurs verticaux au pas de 60,9 pt, page 2 = 7 piles (12+7 = 19 dans). A4 paysage (841,89 × 595,28 pt), 12 cases/pile de 43,94 pt. Le titre vertical (fs 20) et l'accordage (fs 14) sont répétés sur chaque page.

Ces mesures (かぎやで風節.pdf, テスト節.pdf) servent au calibrage du rendu ; elles ne sont pas des spécifications utilisateur.

- Rendu PDF ruby STRICTEMENT LINÉAIRE : `top_caractère = 36,9 + 2,74 + 14,646 × unités` (58 caractères, résidu max 0,00 pt). Unité = hauteur_case/3 = 43,94/3 = 14,646 pt.
- Grille stricte de 3 lignes ruby par case (fractions 0,06 / 0,40 / 0,73), aucun arrimage syllabe↔note — champ texte vertical libre, placement à la demi-unité près (fractions 0,06–0,90).
- Ruby : police IPAexMincho 11 pt (ratio vs note fs 17 = 0,65 ; ratio vs hauteur de case = 0,25). Le JSON dit `lyricsFontSize: "10pt"` mais le ruby rendu est à 11 pt.
- Colonne marker : sous-colonne de 24,1 pt à droite de chaque pile (largeur pile 52,4 = 28,3 notes + 24,1 marker). Ruby dessiné à +3,7 pt du bord gauche de la sous-colonne marker.
- Avance par caractère pleine largeur : 14,646 pt (1,33 × fs ruby), quelle que soit l'appartenance au token.
- Petits kana : +12,99 pt sous le caractère précédent (tuck optique de 1,65 pt) et +1,12 pt à droite ; le caractère suivant reprend sa position de grille. Mesuré sur 17 instances, identique au centième. Portama ne tuck que les petits kana, sans notion de syllabe.
- ー (chōonpu) absent du corpus : comportement non mesuré.
- Géométrie du PDF (A4 paysage, TCPDF) : cadre 28,3–819,2 × 28,3–575,4 pt ; piles au pas de 60,9 pt, cadre 52,4 pt (notes 28,3 + marker 24,1) ; 12 piles/page, 12 cases/pile, hauteur 43,94 pt ; notes fs=17, straddle fs=13 ; ratios marker/notes 0,85 (nous 0,5), cell_h/notes 1,55 (nous 1,12), fs/cell_h 0,39 (nous 0,38).
- Géométrie fine des marques (テスト節.pdf) : orn fs 14 (dx +6,16, dy +4,03 ; isSmall 10, dx +8,07) ; acc fs 14 (dx −2,84, dy +4,02 ; isSmall 10, dx −4,84) ; yubii fs 12,5 (dx −15,46, dy +0,93, colonne dédiée à gauche) ; ○/□ fs 9 (marker +14,8 pt, dy +3,3).
- Polices embarquées : Untitled1 (Type0, Identity-H, upem 1024 ; CID = codepoint PUA) pour les notes, IPAexMincho pour le texte. Contours des glyphes de テスト節.pdf extraits (chemins SVG upem 1024) — disponibles pour la rénovation du rendu des ornements.
- Constantes pour un éventuel bloc `::ruby` : ruby_fs/note_fs = 0,65 ; avance ligne = cell_h/3 ; tuck petit kana = 1,18 × fs (notre espacement actuel : syllable_fs × 0,85).

## Constantes de calibrage mesurées sur les scans Nomura-ryu (recherche)

Sources : `samples/nomura-ryu-pdf/かぎやで風節.pdf` (3 pages), `後に屋節.pdf` (2 pages), `恩納節.pdf` (2 pages) — rééditions scannées de planches calligraphiées (~1930). Chaque page PDF A4 **paysage** (841,89 × 595,28 pt) est composée de 5 images JPEG empilées (~841,8 × ~121 pt, opérateurs `cm`/`Do`). Le recueil physique est **portrait**, scanné tourné de 90° : chaque bande JPEG est un **dan (colonne) complet** de la page physique. Échelle : 3396 px ↔ 841,8 pt → **4,04 px/pt** (~290 dpi). Les 3 morceaux choisis commencent en haut de page ; dans les recueils originaux les chansons s'enchaînent en flux continu (nouveau titre en cours de page, « rouleau découpé en feuilles ») — variante non implémentée pour l'instant.

- Page physique : A4 portrait, **5 dan/page** (largeur de bande ~119,5–121,8 pt, la dernière parfois réduite).
- Grille de cases **dans chaque dan** : cases empilées le long de la direction de lecture (haut→bas), séparateurs au pas très stable de **245 px ≈ 60,6 pt** (mesuré sur 50+ intervalles, dispersion 244–247 px). Cases pleines : ~12 par dan courant (max observé 12, souvent moins en fin de morceau), séparées de filets pleine largeur de dan.
- Case : hauteur 245 px ≈ **60,6 pt**, largeur ~128 px ≈ **31,7 pt** — plus haute que large (ratio ≈ 1,9). Le dan contient une sous-colonne **notes** + une sous-colonne **marker** de même largeur (~128 px), séparées par un filet vertical court (voir filets internes détectés à ~135/260/317/381/451 px dans 後に屋節-2) ; groupes de cases + marker séparés par des **marges blanches** entre dans.
- Titre : vertical, en haut à droite de la **première page** de chaque morceau (position à mesurer finement ; non détectée automatiquement sur ces scans).
- Paroles : sur la **dernière page**, à gauche des dernières notes, dans la bande marker (phonétique, boucles, indications de chant spécifiques Nomura-ryu) — bandes marker très chargées.
- Ordre de lecture : droite→gauche (dan 1 = colonne la plus à droite), cases haut→bas dans chaque dan.
- Implications modèle de page : pagination par **nombre de cases par dan** (12 par dan, systématique), **jusqu'à 7 dan/page** ; lorsque nécessaire un dan est retiré (décalé) pour placer le titre et/ou les paroles. Structure différente de Portama (paysage, piles horizontales de cases).
- Spécification utilisateur (à considérer comme la règle, les mesures ci-dessus n'étant que 3 exemples) : chaque page est encadrée par un **filet** (seul le numéro de page est à l'extérieur) — utiliser ce filet comme origine pour le placement relatif de tous les objets. Page toujours portrait. Dans toujours à 12 cases. Composition manuelle (~1930) d'une régularité exceptionnelle.
**Structures exactes vérifiées (description de droite à gauche, haut→bas = ordre de lecture japonais)** :
- かぎやで風節 (3 pages) : p1 = titre + 6 dans ; p2 = 7 dans ; p3 = 6 dans (les 3 dernières cases du 6e dan sont vides mais présentes) + paroles.
- 恩納節 (2 pages) : p1 = titre + 6 dans ; p2 = 6 dans + paroles.
- 後に屋節 (2 pages) : p1 = titre + 6 dans ; p2 = 4 dans (5 cases vides à la fin du 4e dan) + couplets + titre de la chanson suivante (équivalent 1 dan, à ignorer) + couplets suivants (équivalent 1 dan, à ignorer).

En conséquence : le titre occupe l'équivalent d'**1 dan de large** en haut à droite (colonne la plus à droite) ; les paroles occupent l'équivalent d'**1 colonne de dan** en bas à gauche de la dernière page ; une page pleine = 7 dans ; page avec titre ou paroles = 6 dans utiles ; les deux = 5 dans utiles. Cases vides en fin de morceau : présentes mais non remplies.
- Couplets : débutent par un marqueur générique ⚪︎ (un par couplet) ; coût variable — 1 dan en général, jusqu'à 2 dans si les couplets sont très longs.
- Variations d'éditeur : quelques libéralités possibles par rapport à la structure ; le modèle de page doit s'en tenir aux basiques communs à tous les morceaux et ignorer les rares variantes.
**Vérification sur les pages supplémentaires (野村流工工四上巻, fichier temporaire « glissés », 11 pages)** : assemblage des 5 bandes par page en portrait confirme — filet de cadre page (top/bottom ~189 et ~3260 px ≈ 48 pt des bords), grille de cases **12 par dan** (13 filets au pas 245 px, ex. dan complet : 261→507→752→997→1241→1486→1731→1976→2221→2466→2711→2956→3201), sous-colonne marker à droite de chaque dan, plusieurs dans par page (5-7 détectés selon pages, cohérent avec titre/paroles/couplets consommant des colonnes). L'assemblage des bandes JPEG par page PDF est nécessaire pour la mesure : chaque bande PDF (~841,8 × ~121 pt) est une **tranche horizontale** de la page portrait, pas un dan complet (correction de l'interprétation initiale).
