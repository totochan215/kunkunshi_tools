# Référence des mises en page SVG

## Mise en page verticale (portrait)

Le mode vertical reproduit la disposition traditionnelle des kunkunshi : les cases se lisent de haut en bas et de droite à gauche. Un dan correspond à une colonne.

### Structure générale

```
[paroles verticales]  [grille de tablature]  [titre vertical]
        gauche               centre             droite
```

### Constantes de dimensions

- `cell_w = 52` — largeur de case
- `cell_h = 58` — hauteur de case
- `font_size = 22` — taille de police des notes
- `MARGIN_L = 16`, `MARGIN_R = 16`, `MARGIN_T = 16`
- `GAP_HEADER = 30` — espace après l'en-tête, avant la grille
- `header_h = 40` — en-tête réduit en mode vertical avec titre (le titre n'est pas dans l'en-tête mais rendu verticalement à droite). 70 en mode horizontal ou sans titre.
- `marker_w = cell_w // 2` (= 26) quand `@marker on`, sinon 0

### Titre vertical (à droite de la grille)

- `TITLE_W = 36` — largeur de la colonne titre
- `TITLE_GAP = 10` — gap entre grille et titre
- `title_offset = TITLE_W + TITLE_GAP` (= 46) si titre présent, sinon 0
- `TITLE_SPACING = 30` — espacement vertical entre caractères du titre
- `TUNING_SPACING = 22` — espacement vertical entre caractères de l'accordage
- Position x : `tx = total_w - mr - TITLE_W / 2`
- Titre : `font-size = 26`, accordage : `font-size = 15` en gris (#555)
- Genre : rendu verticalement sous l'accordage, `font-size = 15`, gris plus clair (#777)
- L'accordage commence après le dernier caractère du titre + 20px, le genre après l'accordage + 15px

### Grille de tablature

- Les colonnes sont disposées de droite à gauche (colonne 0 = la plus à droite)
- Chaque colonne contient `rows_per_col` cases (défaut 12, configurable via `@cols`)
- `group_w = cell_w + marker_w` (78 avec marker, 52 sans)
- Position x de la colonne ci : `x = total_w - mr - title_offset - (ci + 1) * group_w`
- Deux passes : d'abord tous les rectangles (grille), puis toutes les notes par-dessus (pour que les notes à cheval ne soient pas masquées par les bordures)

### Paroles verticales (à gauche de la grille)

- `LYRICS_CHAR_SP = 16` — espacement vertical entre caractères
- `LYRICS_LINE_GAP = 10` — gap supplémentaire entre lignes d'un couplet
- `LYRICS_COL_W = 20` — largeur d'une colonne de couplet
- `LYRICS_VERSE_GAP = 16` — gap horizontal entre colonnes de couplets
- `LYRICS_FONT = 13` — taille de police des paroles
- Couleur : `#333`
- Markup de saut de ligne : `|` dans une ligne de paroles force un saut de ligne (la ligne est éclatée à chaque `|`)
- Numéros de couplet : les lignes commençant par `一、`, `二、`, etc. (numéraux CJK + 、) sont détectées via `VERSE_NUM_RE`. La longueur du numéro (ex : 2 pour `一、`) est utilisée comme indent : chaque ligne suivante du couplet reçoit un décalage vertical supplémentaire de `verse_indent * adjusted_sp` pour s'aligner sous le numéro.
- Ajustement de hauteur : désactivé. Les paroles utilisent un espacement fixe (`LYRICS_SP = 18`) et un alignement en haut, sans justification.

#### Calcul de l'espace paroles

1. Compter le nombre total de couplets (lignes vides séparent les couplets)
2. `lyrics_total_w = n_verses * LYRICS_COL_W + (n_verses - 1) * LYRICS_VERSE_GAP`
3. `lyrics_offset = lyrics_total_w + 12` (gap de 12 entre paroles et grille)
4. `total_w` inclut `lyrics_offset`, ce qui décale automatiquement la grille vers la droite

#### Positionnement des couplets

- Chaque couplet est une colonne verticale, disposée de droite à gauche
- Couplet 0 (verse 0) = le plus proche de la grille (à droite), couplet n-1 = le plus à gauche
- Position x du couplet vi : `vx = ml + lyrics_total_w - vi * (LYRICS_COL_W + LYRICS_VERSE_GAP) - LYRICS_COL_W / 2`
- Les caractères sont écrits de haut en bas dans chaque colonne, avec `LYRICS_LINE_GAP` entre les lignes du couplet
- Les paroles sont rendues après la grille, avant le titre

### Marques de répétition (flèches)

Les marqueurs `|:` (début) et `:|` (fin) peuvent être attachés aux tokens (`|:工`, `合/尺:|`) ou utilisés comme tokens autonomes. Le convertisseur les détache avant le rendu des notes via `_strip_repeat_marks()`.

Rendu en mode vertical : les flèches sont placées dans la colonne marker (à droite de chaque pile de cellules, largeur `marker_w`), pas dans les cases de notation ni dans l'espace titre.
- Position x : `x + cell_w + marker_w / 2` (centre de la colonne marker de la pile correspondante)
- ↓ (début) : part de 85% du haut de la case (`cy + cell_h * 0.15`)
- ↑ (fin) : part de 85% du bas de la case (`cy + cell_h * 0.85`)
- Taille : `fs` (même taille que les notes), police serif, couleur noire
- Les flèches ne s'affichent que si `@marker on` (sinon `marker_w = 0`)

Rendu en mode horizontal : les flèches sont placées à l'intérieur de la case, sur le bord droit (`x + cell_w * 0.85`), mêmes positions verticales.

Fonction de rendu : `_render_repeat_arrow(out, x, cy, cell_h, fs, arrow_type)` où `cy` est le top de la case et `arrow_type` est `'start'` (↓) ou `'end'` (↑).

## Largeur totale

`total_w = max_cols * group_w + ml + mr + title_offset + lyrics_offset`

### Rotation des parenthèses en mode vertical

En typographie japonaise verticale, les parenthèses （）, (), les crochets 「」 et 『』 doivent être pivotés de 90° dans le sens horaire. Le convertisseur les détecte via `VERTICAL_ROTATE_CHARS = set("（）()「」『』")` et applique `transform="rotate(90 x cy)"` sur l'élément `text` SVG, où `cy` est le centre visuel approximatif du glyphe (`y - fs * 0.35`). Cette rotation s'applique au titre, à l'accordage et aux paroles.

### Syllabes vocales dans la colonne marker

Les syllabes vocales sont rendues dans la colonne marker (largeur `marker_w`) à droite de chaque pile de cases. Chaque syllabe est un caractère double-largeur (hiragana/katakana) positionné à la même hauteur verticale que la note correspondante.

- Taille de police : SYLLABLE_FS = min(int(cell_h * 0.35), int(marker_w * 0.8)) ≈ 20px avec les valeurs par défaut
- Position x : centre de la colonne marker = `x + cell_w + marker_w / 2`
- Position y : même que la position verticale de la note correspondante dans la case
- Couleur : noire (#000) ou gris foncé (#333)
- Police : serif (même que les notes) ou police japonaise si configuré

Les syllabes peuvent chevaucher la bordure inférieure de la case. Jusqu'à 4 syllabes ou plus peuvent être empilées verticalement dans une seule case, espacées de `SYLLABLE_FS * 0.9` pour éviter le chevauchement visuel.

### Hauteur totale

`total_h` est calculée en cumulant : en-tête, sections tab (max_col_height * cell_h), et au minimum la hauteur du titre vertical.
Les paroles verticales n'ajoutent pas de hauteur (elles s'alignent sur la hauteur de la grille).

## Mise en page horizontale (landscape)

TODO:
