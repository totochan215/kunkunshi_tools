# Architecture du convertisseur Python

Convertisseur principal : `kkml2svg.py` (Python 3 autonome, ~1770 lignes). Ce dépôt est la source de vérité du code.

## CLI

```bash
python3 kkml2svg.py chanson.kkml -o chanson.svg
python3 kkml2svg.py chanson.kkml            # -> chanson.svg
cat chanson.kkml | python3 kkml2svg.py -     # stdin -> stdout
```

Options : `-o output`, `-c cols`, `-l vertical|horizontal`

## Structure du code

### 1. Parseur KKML (`parse_kkml`, lignes ~129-210)
- Classes `Song` (meta, blocks, cols, layout) et `Block` (kind, label, lines)
- Lit ligne par ligne : commentaires `#`, métadonnées `@`, blocs `::kind`, fermeture `::`
- Blocs supportés : `tab`, `lyrics`, `tab-lyrics`, `vocal`, `section`
- `::vocal` se paire au bloc `::tab` précédent : chaque ligne vocale est aplatie avec padding par ligne (`-`) sur la structure de la ligne de tab de même index ; l'excédent est tronqué. La syllabe i reste alignée sur la note i.

### 2. Rendu SVG (`render_svg`, ~212-308)
- Regroupe les blocs en sections 4-uplets `(section_title, content, kind, vocal_data)`
- `has_vocal = any(s[3] or s[2] == "vocal")` → active automatiquement la colonne marker
- Constantes de rendu vocal : `SYLLABLE_FS = min(int(cell_h * 0.35), int(marker_w * 0.8))`
- Route vers `_render_vertical` ou `_render_horizontal`

### 3a. Rendu vertical (`_render_vertical`, ~309-580)
- Offsets `title_offset`, `lyrics_offset`, `marker_w = cell_w // 2` si marker
- Helpers : `_wrap_vertical` (découpage en colonnes de N), `_split_verses` (couplets)
- Titre vertical à droite, paroles verticales à gauche

### 3b. Rendu vocal (`_draw_vertical_vocal`, ~613 + `SMALL_KANA`)
- Un token = une syllabe, rendu dans la colonne marker centré sur la note
- Token multi-caractères empilé : caractère principal aligné sur la note, caractères combinants dessous (espacement `syllable_fs * 0.85`), ー pivoté 90°
- Chevauchement du bord inférieur de case accepté

### 3c. Rendu horizontal (`_render_horizontal`, ~794)
- Mode songbook : gauche→droite, haut→bas. Vocal horizontal non implémenté (priorité au vertical)

### Fonctions de dessin
- `_draw_vertical_tab` — grille verticale, deux passes (rectangles puis notes) ; rend aussi les données vocales pairées
- `_draw_vertical_tab_lyrics` — grille + positions (haut) + syllabes (bas)
- `render_cell` (~1147) — rend un token (voir ci-dessous)
- `_note_svg` — rendu d'une note unique
- `_render_techniques` — souhou autour de la cellule ; suffixes avec `dx/dy/scale/rotate` individuels, paramètre `text_w` pour multi-caractères
- `_strip_repeat_marks` + `_render_repeat_arrow` — marques `|:`/`:|` détachées des tokens, flèches ↓/↑ rendues dans la colonne marker
- `_render_end_circle` — cercle de fin
- `_render_vertical_ruby` / `_render_vertical_text` / `_render_horizontal_ruby` / `_render_horizontal_text` — texte vertical/horizontal (titres, paroles, ruby)

### Tokens gérés par `render_cell` (ordre de traitement)

1. Marques de répétition détachées avant traitement (`_strip_repeat_marks`)
2. Cas spéciaux : EMPTY (`-`), SUSTAIN (`.` → ・), REST (◯/variants)
3. Suffixes de technique extraits de la fin du token
4. `尺♯` selon `@shaku_sharp` (jamais entouré)
5. Accords `A-B` / `A-B-C` (séparateur `-`, max 3 notes) : notes empilées à 72%
6. 下老 et positions hautes `イX`/`ロX` : un seul `<text>` avec `textLength` + `lengthAdjust="spacingAndGlyphs"` (下老 demi-largeur, positions hautes 120%)
7. イ下尺 : 3 caractères condensés (イ下尺), textLength 180%, sans cercle
8. Croche `A/B` (note principale + à cheval), shuffle `A:B` (deux notes empilées)
9. Note simple centrée ; ornement multi-caractères empilé

### Constantes notables
- `POSITION_CHARS`, `REST_VARIANTS`, `TECHNIQUE_SUFFIXES` (uchi-utu `*`, kaki-utu `^`, aki-utu `v`, kachi-utu `<`, kuubanchi `s`, taachi `=`)
- `HIGH_PREFIX_I` / `HIGH_PREFIX_RO` (positions hautes イ/ロ + kanji compatibles)
- `FONT_STYLES` : serif (défaut), mincho, gothic (`@font_style`)
- `VERSE_*` : regex de numéros de couplet, puces, genre (男/女)

## Paramètres par défaut

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| cell_w | 52 | largeur de case |
| cell_h | 58 | hauteur de case |
| font_size | 22 | taille police notes |
| cols | 12 | lignes par colonne (vertical) — défaut depuis le 14 sept. 2026 (avant : 9) |
| marker_w | cell_w // 2 | colonne marker (auto si ::vocal) |

## Convertisseur Portama → KKML

Script séparé `portama2kkml.py` (script autonome).

- Mapping PUA → kanji (voir [format Portama](portama-format.md))
- Paires (main, straddle) → noires, croches (A/B) ou shuffles (A:B) selon `isSmall`
- `acc: "sharp"` → 尺♯, `orn: "u"` → suffixe `*`
- `repeatStart/repeatEnd` → `|:` / `:|`
- `choshi` → `@tuning`, `cellsPerDan / 2` → `@cols`
- N'exporte pas encore `allRubyData` (proposition `::ruby` / conversion `::vocal`, voir `kkml-format.md`)
