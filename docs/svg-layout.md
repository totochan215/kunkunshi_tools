# Référence des mises en page SVG

## Cadre et hanmen (générique, tous les layouts)

Toutes les mises en page partagent le même modèle de cadre (`LayoutSpec`) :

- les **marges** (`margin_t/b/l/r`) écartent le **cadre** du bord de la feuille : `frame_rect() = (margin_l, margin_t, page_w − margin_r, page_h − margin_b)` (en pt) ;
- à l'intérieur du cadre, le **padding** (`pad_t/b/l/r`) définit le **hanmen** réel : `hanmen_rect() = cadre diminué du padding` ;
- le cadre est **tracé** (filet `frame_color` × `frame_width`, helper `_draw_frame`) seulement si `frame_width > 0` — nomura : 1,5 pt `#333333` ; chindami/tuto/mega/vertical/horizontal : 0 par défaut. **`@frame_width 0` = cadre non affiché** : avec padding = 0, le cadre virtuel se confond alors avec le hanmen de la page. `@frame_color`/`@frame_width` surchargent le défaut du layout.
- En page libre (vertical, horizontal : `page_w = 0`), le cadre n'est pas tracé et le hanmen = marges + padding (padding 0 par défaut → comportement historique).

> **Vocabulaire JLreq** : dans les mises en page verticales, une **LIGNE (行)** est l'axe du flux de lecture (vertical) ; 行頭 = haut de la pile, 行末 = bas, l'avance de ligne (行送り) est horizontale droite→gauche. « Colonne » ne décrit que la position sur la page (colonne titre, colonne marker) : un dan est une colonne par sa position et une ligne par sa nature. La hauteur d'une pile de paroles est sa longueur de ligne (行の長さ).

> **Modèle page → bloc → dan** (2026-11-26) : une **page** contient un ou plusieurs **blocs** de tablature (`blocks` ; taille et comportement fixés par le layout — mega : 2 blocs A3 empilés, sinon bloc unique) ; un **bloc** contient au plus `dans_per_block` **dans** (0 = illimité, page de taille libre), avec sa politique d'ajustement fixée par le layout ; un **dan** contient au plus `cells_per_dan` **cases** (personnalisation par bloc à terme). La capacité de page en dans n'est plus une notion primitive : elle est **dérivée**, `page_dans_cap = blocks × dans_per_block` (0 = illimitée). Chaque mise en page a un **mode d'écriture unique** (`writing_mode` = `vertical` ou `horizontal`, cf. JLreq — seul le numéro de page fait exception). Conséquence : `@dans_per_page` / `-p` est **déprécié** — conservé comme simple plafond de la capacité dérivée (vertical/tuto/mega), sans effet quand la page est imposée (nomura/chindami/horizontal).

## Métadonnées et sections rendues (générique, tous les layouts)

Chaque mise en page déclare dans son `LayoutSpec` ce qu'elle affiche, en surcharge des constantes globales :

- **`meta_order`** : quelles métadonnées de `META_ORDER` (`author`, `composer`, `lyricist`, `genre`, `origin`, `choshi`) sont affichées, et dans quel ordre. `@title` et `@speed` restent toujours affichés ; `@source`/`@comment` jamais. Défaut : `META_ORDER` complet (vertical, horizontal) ; tuto : genre → auteur → compositeur → parolier → origine → accordage (sous le tempo) ; mega : genre → auteur → accordage (en bas de la colonne titre) ; nomura : accordage seul ; chindami : genre + accordage (colonne genre intercalée entre le bloc de tab et la colonne titre).
- **`render_sections`** : quels types de sections (`SECTION_KINDS` = `part`, `tab`, `vocal`, `lyrics`, `block`, `page`) sont rendus. Défaut : toutes ; tuto : `tab` + `vocal` (`::lyrics` exclu). Une `::vocal` rattachée à un `::tab` est rendue avec lui si le layout déclare `vocal` (tuto : en bas de case), sinon elle est ignorée — `tab` et `vocal` se filtrent séparément ; l'inverse (vocal sans tab) n'a pas de rendu : une `::vocal` sans `::tab` n'est jamais dessinée (alignement sur la tablature).
- **`render_koe` / `render_yubii`** : symboles koedashi/koekiri (○/□) et doigtés (㊀-㊃) rendus dans les cases — off en tuto.

## Mises en pages standard

### Mise en page verticale standard

Le mode vertical reproduit la disposition traditionnelle des kunkunshi : les cases se lisent de haut en bas et de droite à gauche. Un dan correspond à une colonne sur la page, c'est-à-dire une ligne (行) vis-à-vis du flux : lecture de haut (行頭) en bas (行末) le long de la ligne, avance de ligne (行送り) horizontale droite→gauche.

#### Structure générale

```
[paroles verticales]  [grille de tablature]  [titre vertical]
        gauche               centre             droite
```

#### Constantes de dimensions

- `cell_w = 52` — largeur de case
- `cell_h = 58` — hauteur de case
- `font_size = 22` — taille de police des notes
- `margin_l = 16`, `margin_r = 16`, `margin_t = 16`
- `gap_header = 30` — espace après l'en-tête, avant la grille
- `header_h = 40` — en-tête réduit en mode vertical avec titre (le titre n'est pas dans l'en-tête mais rendu verticalement à droite). 70 en mode horizontal ou sans titre. En vertical avec titre, `header_h = 10` : l'en-tête haut-gauche est vide, toutes les métadonnées secondaires (`@lyricist`, `@composer`, `@origin`) étant rendues verticalement dans la colonne titre.
- `marker_w = cell_w // 2` (= 26) quand `@marker on`, sinon 0

Schéma coté de ces constantes (style figures du [JLREQ](https://www.w3.org/TR/jlreq/) : éléments en gris foncé, cotes et flèches en bleu) : [svg-layout-vertical.svg](svg/svg-layout-vertical.svg). Les 6 mises en page ont leur schéma (`svg/svg-layout-<layout>.svg`), générés par `python3 docs/svg/make_svg_layout_figures.py`.

#### Titre vertical (à droite de la grille)

- `title_w = 36` — largeur de la colonne titre
- `title_gap = 10` — gap entre grille et titre
- `title_offset = title_w + title_gap` (= 46) si titre présent, sinon 0
- `title_spacing = 30` — espacement vertical entre caractères du titre
- `tuning_spacing = 22` — espacement vertical entre caractères de l'accordage
- `md_spacing = 15` — avance avant chaque bloc de métadonnées (titre → 1re méta, méta → méta, @choshi compris ici), identique pour tous les blocs
- Position x : `tx = total_w - mr - title_w / 2` (colonne 1) ; chaque colonne supplémentaire est décalée de `title_w` vers la gauche
- Titre : `font-size = 26`, accordage : `font-size = 15` en gris (#555)
- **Ordre commun des blocs** (`META_ORDER`, identique en horizontal) : titre → auteur (`@author`) → compositeur (`@composer`) → parolier (`@lyricist`) → genre → origine (`@origin`) → accordage (`@choushi`, en dernier). Le genre n'est pas répété s'il égale l'auteur. Métadonnées secondaires : `font-size = 15`, gris clair (#777), accordage #555 ; l'en-tête haut-gauche est vide en vertical
- **Tempo** `@speed` : `♩=120` rendu HORIZONTAL (fs 12, sans espace, `<text>` sans `transform`), `text-anchor="middle"` exactement sur la centerline de base du titre (hors ruby), juste avant le bloc accordage `@choshi` (bloc spécial du flux vertical : espacement nul)
- **Flux de blocs (jamais scindés)** : les blocs se succèdent dans la MÊME ligne (行 — une seule colonne sur la page), sous le titre (+ 15 px d'avance), autant que de besoin, SANS repli à la ligne suivante (règle alignée des layouts libres : les dimensions dépendent du contenu). La hauteur de page grandit pour couvrir tout le flux : `title_total_h = somme(avance + hauteur de bloc) + 10`
- Rotation verticale (typographie japonaise) : parenthèses （）() et guillemets 「」『』 pivotés de 90° (sens horaire) ; le signe ー (chōonpu, U+30FC) est également pivoté de 90° (barre verticale). Depuis 2026-11-25 (règle JLREQ du texte vertical appliquée au romaji) : le latin et les chiffres HALF-WIDTH `A-Za-z0-9` sont aussi pivotés de 90°. Pas de pivot pour `-` ASCII, pour 一, ni pour le latin PLEINE chasse ＡＢＣ (U+FF21+). L'avance verticale d'un latin half-width pivoté est sa CHASSE (sa largeur de glyphe, `fs × LATIN_WIDTH_EM`, table heuristique style Times : i/l/j/t 0,28 em, m 0,78, W 0,94, défaut 0,5 em — ajusté pour les polices à chasses variables), pas le pas fixe `sp` ; kana, pleine chasse et signes pleine chasse gardent `sp`. Fonction `_vstep`, appliquée dans `_plan_vertical_ruby`, `_render_vertical_text` et `_draw_vertical_vocal`. Les runs de latins half-width consécutifs sont émis en **UN SEUL bloc `<text>` avec un unique `transform="rotate(90 x cy)"`** (`_vertical_rotated_run`) : c'est le moteur de rendu qui fait avancer les glyphes avec leurs vraies largeurs (+ crénage), comme à l'horizontal — le pivotage lettre par lettre à chasses approchées décalait jusqu'à 8,7 pt par lettre et élargissait « composites » de +7,6 % à fs 26 (mesuré 2026-11-25). `LATIN_WIDTH_EM` = vraies métriques Times-Roman (AFM WX/1000), utilisée seulement pour l'avance du run entier (`_vstep`) entre deux caractères non latins.
- **Blocs `<text>` groupés** (`_vertical_grouped_text`) : chaque bloc de la ligne (titre compris) a ses caractères de base regroupés en UN SEUL élément `<text>` avec listes `x="x x …"` (répétée : indispensable, sinon chaque glyphe conserve l'avance naturelle du précédent et le texte part en escalier) et `y="y1 y2 …"` (SVG 1.1) — un bloc de texte copiable d'une pièce par métadonnée. Chaque annotation ruby est un bloc `<text>` indépendant à droite de sa base (géométrie de `_render_vertical_ruby`, unifiée via `_plan_vertical_ruby`). Les caractères pivotés (ー, parenthèses, guillemets, romaji/chiffres half-width) sortent du bloc et sont rendus en éléments `<text>` individuels avec `transform="rotate(90 x cy)"` (l'attribut `rotate` par glyphe ayant une sémantique variable selon les moteurs de rendu).

**Écartement générique des groupes rubyés (règle Word/LibreOffice, `_plan_vertical_ruby`)** : JAMAIS d'écartement des caractères au sein d'un groupe rubyé — ce sont les groupes (bases groupées) qui s'écartent, de manière à ce que les blocs ruby se suivent en flux continu au rythme du flux intra-bloc : baseline du bloc n+1 ≥ baseline du dernier glyphe du bloc n + `ruby_sp` (garde-fou minimal `ruby_fs + 0,4·ruby_fs`). Chaque bloc ruby est centré sur l'ENCRE de sa base : les glyphes sont horizontaux empilés (encre de y−0,88em à y+0,12em, centre à y−0,38em), donc le centrage compense `0,38 × (fs − ruby_fs)` — un centrage sur les seules baselines fait paraître le ruby trop bas. Quand le flux l'exige, le groupe de base est poussé vers le bas pour que son ruby prenne la suite du flux (les caractères d'un groupe restent à `sp`). Le plan est partagé par le rendu per-caractère (`_render_vertical_ruby`, donc les paroles verticales) et les blocs groupés (métadonnées) ; les hauteurs de page (`title_total_h`) utilisent les hauteurs planifiées réelles. En HORIZONTAL, la même règle s'applique via `_plan_horizontal_ruby` (ruby AU-DESSUS de la base, ligne `ruby_y = y − 0,95·fs`) : les blocs ruby se suivent en flux continu (bord gauche du bloc n+1 ≥ bord droit du bloc n + `gap = 0,4·ruby_fs`), centrés sur leur base quand le flux le permet ; les avances `_char_w` (CJK 1em, latin 0,55em) tiennent lieu de boîtes, le centrage sur les avances valant centrage sur l'encre. Valable pour le titre horizontal ET toutes les métadonnées d'en-tête (rendues par `_render_horizontal_text`).

En-tête horizontal : titre à gauche (26 pt, ruby au-dessus), puis les blocs de métadonnées dans l'ordre commun `META_ORDER` (accordage 15 pt #555, autres 12 pt #777, blocs jointés par deux espaces) : tous sur la ligne du titre, centrés verticalement sur lui (centre d'encre aligné : baseline = baseline titre − `0,38 × (26 − fs)`), à la suite les uns des autres, SANS repli (règle alignée : la page s'élargit à la largeur du flux, jamais de seconde ligne). Marges VERTICALES recyclées de la mise en page verticale, transposées : l'air entre le bas d'encre du titre et la grille vaut `title_gap + (title_w − 26) // 2` (= 15 px, comme l'air colonne titre → grille en vertical), intégré dans `header_h` (calculé dans `_render_horizontal`, `gap_header = 0`) ; l'air entre le bas de la tablature (ligne marker) et le premier couplet vaut `12 + LYRICS_COL_W` (même formule que `lyrics_offset − lyrics_total_w` en vertical), le `+6` résiduel du bloc tab et l'ascension d'encre du premier vers étant compensés dans `GAP_TAB_LYRICS`. Pas de flux en mega/chindami/nomura (`cols = None`).

#### Grille de tablature

- Les colonnes sont disposées de droite à gauche (colonne 0 = la plus à droite)
- Chaque colonne contient `cells_per_dan` cases (défaut 12, configurable via `-c` en CLI)
- `group_w = cell_w + marker_w` (78 avec marker, 52 sans)
- Position x de la colonne ci : `x = total_w - mr - title_offset - (ci + 1) * group_w`
- Deux passes : d'abord tous les rectangles (grille), puis toutes les notes par-dessus (pour que les notes à cheval ne soient pas masquées par les bordures)

#### Paroles verticales (à gauche de la grille)

- Taille de police des paroles : `LYRICS_FS = int(fs * ratio)` avec `ratio` selon `@lyrics_size` (`small` = 50 %, `medium` = 75 % défaut, `big` = 100 %) — 16 avec fs = 22 en `medium`
- Espacement vertical entre caractères : `LYRICS_SP = int(LYRICS_FS * 1.2)` (19 par défaut)
- Largeur d'une colonne de couplet : `LYRICS_COL_W = int(LYRICS_FS * 1.33)` (21 par défaut)
- Gap horizontal entre colonnes de couplets : `LYRICS_VERSE_GAP = int(LYRICS_COL_W * 0.8)` (16 par défaut)
- Couleur : `#333333`
- Markup de saut de ligne : `|` dans une ligne de paroles force un saut de ligne (la ligne est éclatée à chaque `|`)
- Numéros de couplet : les lignes commençant par `一、`, `二、`, etc. (numéraux CJK + 、) sont détectées via `VERSE_NUM_RE`. La longueur du numéro (ex : 2 pour `一、`) est utilisée comme indent : chaque ligne suivante du couplet reçoit un décalage vertical supplémentaire de `verse_indent * adjusted_sp` pour s'aligner sous le numéro.
- Hayashi （…） : une ligne ENTIÈREMENT entre parenthèses (pleine ou demi-chasse, annotations ruby autorisées, ex. `（いめのかじありよ船《ふに》）` dans だんじゅかりゆし) est une INTERJECTION entre deux couplets (`_is_hayashi`) : elle ferme le couplet courant (`_split_verses`), forme une unité à part et n'est PAS un couplet — pas de marqueur, ne compte pas dans la numérotation ni dans l'indentation cible de la section (`_verse_indent_target`). Règle typo japonaise du rendu (dans `_lyrics_columns_layout`) : la parenthèse OUVRANTE pend juste AU-DESSUS du premier caractère du texte (une position) et le texte s'aligne sur le niveau des continuations indentées de la section (`base_indent`) — réalisé au niveau des données par `base_indent - 1` espaces pleine chasse en tête de ligne.
- Indentation uniforme (vertical/nomura/chindami) : les en-têtes de couplets occupent TOUJOURS 3 caractères pleine chasse (marqueur + espaces pleine chasse de remplissage : `ー、　`/`女、　`/`男、　`/`十二、`/`男女、`), donc les lignes de continuation s'indentent à la position 3, le long de la ligne depuis 行頭 (`_verse_indent_target` = max(3, plus long marqueur)) — un marqueur suivi du texte sur la même ligne est MATERIALISÉ en « marqueur + espaces jusqu'à 3 » par `_pad_inline_marker` (appelé par `_lyrics_columns_layout`, donc dans tous les layouts : le texte démarre au caractère 4, avec ou sans espace pleine chasse explicite dans la source ; idempotent ; un marqueur seul sur sa ligne et un marqueur de ≥ 3 caractères ne sont pas touchés ; ex. 安波節 `一、安波ぬ…` et `一、　安波ぬ…` rendent pareil). Les marqueurs de symbole incluent ⚫⚪○・● (⚪︎ avec sélecteur de variante géré par `_pad_inline_marker`, ex. かぎやで風節 `⚪︎　今日の…`). - Ajustement de hauteur : désactivé. Les paroles utilisent un espacement fixe (`LYRICS_SP = int(LYRICS_FS * 1.2)`, 19 par défaut) et un alignement en haut, sans justification.

##### Calcul de l'espace paroles

1. Compter le nombre total de couplets (lignes vides séparent les couplets)
2. `lyrics_total_w = n_verses * LYRICS_COL_W + (n_verses - 1) * LYRICS_VERSE_GAP`
3. `lyrics_offset = lyrics_total_w + 12` (gap de 12 entre paroles et grille)
4. `total_w` inclut `lyrics_offset`, ce qui décale automatiquement la grille vers la droite

##### Positionnement des couplets

- Chaque couplet est une ligne verticale (行) — une colonne par sa position x —, disposée de droite à gauche (avance de ligne 行送り horizontale)
- Couplet 0 (verse 0) = le plus proche de la grille (à droite), couplet n-1 = le plus à gauche
- Position x du couplet vi : `vx = ml + lyrics_total_w - vi * (LYRICS_COL_W + LYRICS_VERSE_GAP) - LYRICS_COL_W / 2`
- Les caractères sont écrits de haut (行頭) en bas (行末) dans chaque ligne, avec `LYRICS_SP` entre les segments (lignes source) du couplet
- Les paroles sont rendues après la grille, avant le titre

#### Marques de répétition (flèches)

Les marqueurs `|:` (début) et `:|` (fin) peuvent être attachés aux figures (`|:工`, `合/尺:|`) ou utilisés comme symboles autonomes. Le convertisseur les détache avant le rendu des notes via `_strip_repeat_marks()`.

Rendu en mode vertical : les flèches sont placées dans la colonne marker (à droite de chaque pile de cellules, largeur `marker_w`), pas dans les cases de notation ni dans l'espace titre.
- Position x : `x + cell_w + marker_w / 2` (centre de la colonne marker de la pile correspondante)
- ↓ (début) : part de 85% du haut de la case (`cy + cell_h * 0.15`)
- ↑ (fin) : part de 85% du bas de la case (`cy + cell_h * 0.85`)
- Taille : `fs` (même taille que les notes), police serif, couleur noire
- Les flèches ne s'affichent que si `@marker on` (sinon `marker_w = 0`)
- Style vectoriel commun aux layouts (flèches `|:`/`:|` et boucles vocales `(:`/`:)`) : coude horizontal/vertical tracé en un seul `<path>` (pas deux segments superposés), trait de même largeur et couleur que la grille du layout appelant (vertical/mega `#bbbbbb` 0,75 pt ou 0,6 pt selon la variante de grille, horizontal `#999999` 0,75 pt, tuto `#333333` 0,6 pt)
- **Ordre des couches (z-order)** : dans tous les layouts, le TEXTE (kandokoro, syllabes vocales, paroles, titres) est systématiquement au-dessus des traits — bordures de cases, filets de lignes/colonnes marker, symboles de boucles (flèches de répétition, répétitions du chant, marqueur de fin). Chaque grille est rendue en passes : 1) bordures (cases + bande marker), 2) symboles de contrôle, 3) notes, 4) vocaux. Exemple : une note à cheval (straddle) sur la bordure droite d'une case n'est jamais recouverte par le filet de la case suivante.

Rendu en mode horizontal : les flèches sont placées dans la LIGNE marker sous la rangée de cases (`_h_repeat_arrow`, transposée) ; voir « Mise en page horizontale standard ».

Fonction de rendu : `_render_repeat_arrow(out, x, cy, cell_h, fs, arrow_type)` où `cy` est le top de la case et `arrow_type` est `'start'` (↓) ou `'end'` (↑).

### Largeur totale

`total_w = max_cols * group_w + ml + mr + title_offset + lyrics_offset`

#### Rotation des parenthèses en mode vertical

En typographie japonaise verticale, les parenthèses （）, (), les crochets 「」 et 『』 doivent être pivotés de 90° dans le sens horaire ; de même le signe ー (chōonpu, U+30FC), barre horizontale en horizontal, devient une barre verticale. Le convertisseur les détecte via `VERTICAL_ROTATE_CHARS = set("（）()「」『』ー" + "A-Za-z0-9")  # + romaji/chiffres half-width pivotés depuis 2026-11-25` et applique `transform="rotate(90 x cy)"` sur l'élément `text` SVG, `cy` étant le centre visuel approximatif du glyphe (`y - fs * 0.35`). Cette rotation s'applique au titre, à l'accordage, aux métadonnées secondaires et aux paroles. Pas de pivot pour `-` ASCII, pour 一 ni pour le latin pleine chasse ＡＢＣ.

#### Syllabes vocales dans la colonne marker

Les syllabes vocales sont rendues dans la colonne marker (largeur `marker_w`) à droite de chaque pile de cases. Chaque syllabe est un caractère double-largeur (hiragana/katakana) positionné à la même hauteur verticale que la note correspondante.

- Taille de police : SYLLABLE_FS = min(int(cell_h * 0.26), int(marker_w * 0.8)) ≈ 15px avec les valeurs par défaut
- Position x : centre de la colonne marker = `x + cell_w + marker_w / 2`
- Position y : même que la position verticale de la note correspondante dans la case
- Couleur : noire (#000) ou gris foncé (#333333)
- Police : serif (même que les notes) ou police japonaise si configuré

Les syllabes peuvent chevaucher la bordure inférieure de la case. Jusqu'à 4 syllabes ou plus peuvent être empilées verticalement dans une seule case, espacées de `SYLLABLE_FS * 0.9` pour éviter le chevauchement visuel.

#### Hauteur totale

`total_h` est calculée en cumulant : en-tête, sections tab (max_col_height * cell_h), et au minimum la hauteur du titre vertical.
Les paroles verticales n'ajoutent pas de hauteur (elles s'alignent sur la hauteur de la grille).

#### Cas des positions hautes + 下老 ou 下尺

Le préfixe イ ou 口 peut aussi s'appliquer à 下老 et 下尺. La figure fait alors 3 caractères (ex. イ下尺 ou ロ下尺). Rendu : les 3 caractères condensés via `textLength` à 180% de la largeur d'un kanji avec `lengthAdjust="spacingAndGlyphs"`. Le 尺 n'est PAS entouré d'un cercle dans ce composé : le 下 reste visible et le rendu suit le patron de 下老 élargi à 3 caractères. Le composant est large mais nécessaire (Ex. utilisé dans Hiyamikachibushi).

Rendu : préfixe et kanji condensés via un seul `<text>` avec `textLength` et `lengthAdjust="spacingAndGlyphs"`. 2 caractères → 120% de fs, 3 caractères (イ下尺) → 180% de fs. Les suffixes de technique s'appliquent (ex : イ尺' = イ尺 + uchi-utu) ; en multi-caractères, la marque top-right est posée au centre du token (ancre `start`, elle surplombe le caractère de droite), la marque bottom-left en retrait à gauche du token (ancre `end` à cx − 0,34·fs). Pour イ下尺 / ロ下尺, pas de cercle : les 3 caractères sont rendus condensés (le 下 reste visible).

#### Suffixes de technique (souhou) — positionnement

Calibrage Inkscape de nov. 2026 (grille de test + かぎやで風節, てぃんさぐぬ花, 十九の春). Formules dans `_tech_char_pos` (kkml2svg.py). `note_fs` = taille réelle de la note porteuse (pleine, croche à cheval `ss`, ou réduite par `s`). Depuis nov. 2026, **tout est relatif à `note_fs`** : taille du glyphe (`tech_fs = int(note_fs·1,1·scale)`) ET tous les offsets (`dx`, `dy`, `drop`, retrait 0,34) sont des fractions de `note_fs` — mêmes constantes globales dans toutes les mises en page (homogène), chaque glyphe garde ses propres offsets selon sa forme. La marque suit donc le coin du kanji quelle que soit sa taille.

- `｀` uchi-utu (`'`) : haut-droit, chevauche le coin du kanji. `tx = cx + 0,58·note_fs` ; `ty = baseline − note_fs + 0,91·note_fs` (la marque descend sur le coin haut-droit, posée sur le sommet de la note). Notes pleines et petites notes calibrées (résidu < 1 px).
- `゜` nuchi-utu (`"`) : à droite de la note, à mi-hauteur du kanji. `tx = cx + 1,125·note_fs`, `ty = baseline + 0,02·note_fs`.
- `⌝` kaki-utu (`^`) : haut-droit, près de la tête de la note. `tx = cx + 0,4633·note_fs`, `ty = baseline − 0,44·note_fs`
  (calibrage complémentaire nov. 2026, correction Inkscape Hiragino Mincho ProN sur nomura 十九の春 : −3/+3 pt sur note à cheval ss=18, reproduit exactement en nomura ; avant : 0,63 / −0,42 avec dy × fs de case).
- `⌞` kachi-utu (`<`) et `V` aki-utu (`v`) : bas-gauche, au contact du kanji. `tx = cx − 0,57·note_fs`, `ty = baseline + 0,44·note_fs` ; en multi-caractères, ancre `end` à cx − 0,34·note_fs`.
- Taille des glyphes : `tech_fs = int(note_fs·1,1·scale)` — uchi/nuchi ≈ 4/3 de la note (scale 1,21), kaki ≈ la note (0,91), kachi/aki ≈ 1,1.

`'` et `^` ne partagent plus de position moyenne : le calibrage a montré des réglages distincts (le `｀` descend chevaucher la note, le `⌝` reste en retrait au-dessus).

#### Pagination multipage

Par défaut, le rendu vertical produit un seul SVG non contraint. Pour une sortie imprimable (PDF, impression), la méta `@dans_per_page N` (**dépréciée** : simple plafond — en vertical la page est libre, `page_dans_cap = 0` = illimité) ou l'option CLI `-p N` / `--dans-per-page N` limite le nombre de dans par page : le rendu produit alors un SVG complet par page (`chanson-1.svg`, `chanson-2.svg`, …).

- Chaque page est un SVG autonome avec ses propres dimensions ; l'en-tête, le titre vertical et la colonne marker sont répétés sur chaque page.
- Les dans ne sont jamais coupés : la découpe se fait entre colonnes.
- Les sections `::lyrics` (paroles verticales) apparaissent sur la première page.
- Référence : les PDF Portama affichent au maximum 12 piles (dans) par page en A4 paysage.

### Mise en page horizontale standard

Schéma coté : [svg-layout-horizontal.svg](svg/svg-layout-horizontal.svg).

Lecture gauche→droite, haut→bas. Depuis la PR tuto, le layout `horizontal` partage avec `tuto` le straddle des croches chevauche la **bordure droite** des cases (`render_cell(..., orient="h")`). Les syllabes `::vocal`, les flèches de répétition et les symboles de répétition du chant sont en revanche dans une **LIGNE marker sous chaque rangée de cases** (transposée de la colonne marker verticale), pas dans les cases : hauteur `marker_h = cell_h // 2`, bordure comme la grille (`#999999`, 0,75 pt), **arrêtée à droite de la dernière case de la rangée** (le dernier dan d'une section peut être incomplet) ; forcée si `::vocal` est présent, sinon pilotée par `@marker` (défaut `on`). Marge droite du layout horizontal élargie à **une demi-case** (`mr = max(margin_r, cell_w // 2)`) : le straddle sur la bordure droite, les ornements et les syllabes vocales peuvent déborder du bloc de tablature à droite, c'est normal.

- Syllabes vocales (`_draw_marker_line_vocal`, transposée de `_draw_vertical_vocal`) : taille `min(26% de cell_w, 80% de marker_h)` ; éléments d'un temps répartis le long de la case (`x_i = cx + cell_w·i/n`, i=0 sous la note principale) ; caractères combinants enfilés vers la droite (`step = 1,15·fs`) ; `ー` non pivoté ; points `・` et texte en #333333 (couleur du texte vocal) ; parenthèses koedashi/koekiri ignorées ici (symboles déjà rendus dans les cases, voir bullet suivant).
- Bornes de chant koedashi/koekiri `○`/`□` (`_draw_marker_line_vocal`) : rendues DANS la case, alignées en x sur l'élément vocal (syllabe ou point, même masqué) auquel la borne est rattachée, et **en y sur la centerline du tiers inférieur de la case** (`y_top − cell_h/6 + ss·0,318`)
- Flèches de répétition (`_h_repeat_arrow`, transposée de `_render_repeat_arrow`) : trait vertical depuis le haut de la ligne (66% de `marker_h`), coude horizontal dans le sens de lecture, un seul `<path>`, triangle creux au bout ; `start` (|:) à 20% de la case pointe vers la droite, `end` (:|) à 80% pointe vers la gauche.
- Répétitions du chant (`_h_vrep_marker`, transposée de `_render_vrep_marker`) : barre verticale, montant horizontal, disque creux (rayon 22% de `marker_h`) ; `end` ( )| ) à 80% de la case vers la gauche, `start` ( |( ) miroir à 20% vers la droite.

En-tête horizontal : voir les paragraphes « Écartement générique des groupes rubyés » et « En-tête horizontal » ci-dessus (ordre commun `META_ORDER`, flux sans repli sur la ligne du titre).

- **Tempo** `@speed` : `♩=120` (fs 12, #555) dans le flux horizontal des métadonnées, à droite du titre, juste avant `@choshi`
- `md_spacing = 20` — espacement horizontal uniforme entre le titre et la 1re métadonnée, et entre chaque bloc de métadonnées du flux

**Paroles horizontales (`::lyrics`) — même règle qu'en vertical, transposée** : chaque ligne verticale (行, délimitée par `|` / `||`, construite par `_lyrics_columns_layout`) devient une LIGNE horizontale ; les segments d'une même ligne se suivent sur la ligne séparés par une espace pleine chasse (transposé de l'espace vertical de 1 `LYRICS_SP` le long de la ligne) ; une ligne qui commence par un marqueur de couplet (一、女、…) s'aligne à gauche (indent 0) et les continuations du couplet s'indentent à la position 3, l'en-tête occupant toujours 3 caractères pleine chasse (indent par couplet = max(3, marqueur), ex. `女、` -> 3, `男女、` -> 3), pas à l'indentation uniforme de la section. Helper unique `_h_lyrics_layout(data, fs, usable_w=None)` → `[(indent, texte)]`, partagé par le rendu et l'estimation de hauteur (`total_h` = lignes × `h_lyrics_sp` + 6). Règle alignée (layouts libres) : PAS de repli — une ligne verticale = une ligne horizontale, aussi longue soit-elle ; la page s'élargit à la ligne la plus longue (`total_w = max(grille, flux métadonnées, paroles) + marges`). Le retour aux atomes (`_h_lyrics_atoms`, insécables) reste implémenté derrière le paramètre `usable_w` pour un éventuel repli explicite. Une ligne vide est insérée automatiquement entre chaque couplet ; ligne blanche (`||`) = ligne blanche. **Interlignes** : transposé de la réservation verticale (`max_ruby_w` réservé en largeur entre les colonnes) — quand une ligne porte un ruby, l'interligne qui la précède s'élargit (`_h_lyrics_pitch` : encre précédente +0,12·fs + ascension ruby 0,95·fs + 0,88·ruby_fs + 2 pt d'air, min. `h_lyrics_sp`), sinon `h_lyrics_sp` ; l'estimation de hauteur compte les mêmes extras.

## Mises en page complexes

### Mise en page Nomura-ryu (`@layout nomura`)

Schéma coté : [svg-layout-nomura.svg](svg/svg-layout-nomura.svg).

Le layout `nomura` émule le format des recueils Nomura-ryu Kunkunshi (野村流工工四) : une page A4 **portrait** encadrée par un filet (seul le
numéro de page –n– est hors du filet), jusqu'à **7 colonnes (dans) par bloc** (`dans_per_block = 7` ; 1 bloc/page, capacité dérivée `page_dans_cap` = 7),
chaque dan étant composé de **12 cases empilées** lues de haut en bas — l'ensemble se lit de
droite à gauche.

- Le **titre** occupe la colonne la plus à droite de la première page du morceau, cette section pouvant également porter des informations complémentaires telles que l'auteur.
- **Accordage** `@choshi` : en bas de la colonne titre (page 1), bas ancré sur le bas de la grille (`grid_y0 + grid_h − 4 − len·20`), même règle qu'en chindami.
- **Tempo** `@speed` : `♩=120` horizontal (fs 12), `text-anchor="middle"` sur la centerline de base du titre (hors ruby), sous le titre (page 1, colonne titre), au-dessus de `@choshi`
- `md_spacing = 8` pt — espacement titre → méta (@choshi ancré en bas de la grille, exclu de cette règle)
- Chaque dan est constitué d'une **pile de cases** et d'une **colonne marker** (même largeur qu'une case), dans laquelle sont placés les boucles de répétitions, les syllabes vocales, les symboles de technique de chant, et la hauteur de chant.
- Les **paroles** occupent les dernières colonnes de la dernière page (chaque couplet y est une ligne (行) verticale — une colonne par sa position). La page étant imposée, une ligne de couplet plus longue que le hanmen (longueur de ligne 行の長さ > hauteur du hanmen) est **repliée en sous-lignes** de ≤ `max_lyr_u = int((grid_h − LYRICS_FS) // LYRICS_SP) + 1` unités (`_cap_lyr_column`, kinsoku JLREQ, défaut `off` en nomura comme avant) — les sous-lignes consomment des dans virtuels comme les lignes pleines (colonnes de la page) ; jamais de débordement du cadre.
- Les dans sont séparés par une marge,
- Pour une régularité de la mise en page, le titre et les paroles occupent des espaces correspondant à des **dans virtuels**, de même largeur qu'un dan, mais sans cases ni marker ni bordures,
- La sortie est automatiquement multipage : chaque page est rendue sous forme d'un SVG
  autonome (`fichier-1.svg`, `fichier-2.svg`…).
- **Numéro de page** : `–n–` hors du cadre, juste au-dessus (baseline `fy0 - 8`, les caractères
  ne touchent pas le filet ; taille 13 pt, comme la métadonnée accordage, champ `page_no_fs` indépendant) ; n pair → aligné à gauche du cadre (`x = fx0`), n impair → aligné à
  droite (`x = fx1`) ; n = `@page_base` (défaut 1) + index de page.

### Mise en page Chindami-Kunkunshi (`@layout chindami`)

Schéma coté : [svg-layout-chindami.svg](svg/svg-layout-chindami.svg).

Le layout `chindami` émule le format des deux recueils Chindami Kunkunshi (ちんだみ工工四百選集), ouvrages connus de nombreux musiciens. La mise en page est au format vertical, avec une section de titre vertical à droite, un section de tablatures verticales au centre, puis une section de paroles verticales.

Les recueils font 23 x 15 cm, en paysage. Les piles comprennent 12 cases, et la colonne marker fait une demi-case en largeur. Les tablatures peuvent déborder sur plusieurs pages au besoin. Le titre est surplombé d'un numéro de morceau. L'accordage `@choshi` est en bas de la colonne titre, **même fs que le titre** (`title_fs = 17,5` pt), aligné horizontalement sur la première colonne du titre (la plus à droite), dernière baseline à **2,3 cm du bord bas de la page** (ancrage page ; variable selon les planches, l’diteur le rabaisse parfois pour faire de la place). Le tempo `@speed` est rendu `♩=120` en horizontal (**fs 10** en chindami), `text-anchor="middle"` sur la centerline de base du titre (hors ruby), sous le titre (page 1), au-dessus de `@choshi` (`md_spacing = 6` pt entre titre et tempo ; `@choshi` ancré à 2,3 cm du bord bas de page, exclu).

- **Page imposée** 23 × 15 cm paysage (viewBox en pt, export Inkscape 600 dpi), sans liseré de page (`frame_width = 0`) ; le cadre virtuel = hanmen (padding 0) est écarté des bords par les marges : marges mesurées au BLOC de tablature (recueil, 2026-11-24) : `spec.margin_t` = 1 cm, `spec.margin_b` = 1,3 cm, `spec.margin_l = spec.margin_r` = 1,5 cm — la grille occupe tout le hanmen (pas de gap entre piles, `dan_gap = 0`).
- Piles de 12 cases (`spec.cells_per_dan`) lues de haut en bas puis de droite à gauche ; colonne marker (~1/2 de case, soit ~1/3 de la pile case+marker) à droite de chaque pile ; jusqu'à **16 piles par bloc** (`spec.dans_per_block = 16` : plafond absolu de la page non extensible — atteint seulement si aucun titre/méta sur la page, sinon le nombre de piles est dérivé de la largeur du bloc ancré ; plus gros bloc constaté dans le recueil). La colonne titre est **ancrée à 0,75 cm du bord droit de la page** (pitch `title_w` = 6 mm hors ruby, mesures 2026-11-25 : 1,5 + 6,0 + 7,5 = 15 mm au total) et ne bouge jamais ; c'est le **bloc de tab qui recule** pour ménager le gap `title_gap` = 1,5 mm avant la colonne (`tab_right_first = min(fx1, colonne_titre_gauche − title_gap)`) ; un titre long accepte un saut de ligne (avance de ligne horizontale vers la colonne suivante) et repousse alors la grille à gauche d'autant (`title_extra_w`). Les piles ne sont JAMAIS décalées par les paroles.
- **Alignements verticaux** : le HAUT D'ENCRE de la première glyphe de chaque ligne de couplets (行頭) est aligné STRICTEMENT sur le haut de la grille. Colonne titre : ancrage PAGE (hanmen = cadre ici) — si `@musicno` est absent ou nul, la première baseline du titre est à **2,1 cm du haut de la page** ; si le numéro existe, il est écrit en HORIZONTAL, **centré sur la colonne titre** (`x = tx`), avec fs = **6 mm** (largeur «99 » = 6 mm, hauteur d’encre ≈ 4 mm) et sa **ligne médiane ~1 mm au-dessus de celle de la 1re cellule** (ancrage page : `y = margin_t + cell_h/2 − 0,1 cm + 0,35·fs`, pas un ancrage sur le bloc de tab) ; le titre démarre **0,4 cm** sous le bas d’encre du n° (baseline = `y_mno + 0,12·fs + 0,4 cm + 0,88·fs_titre`). Mesures 2026-11-25. Numéro = 0 → non écrit ; > 999 → tronqué à la valeur sous les milliers (mod 1000, 0 → non écrit) ; non numérique → rendu tel quel.
- **Colonne genre** : si `@genre` est présent (et distinct de l'auteur), une colonne verticale s'intercale entre le bloc de tab et la colonne titre — gap `genre_gap` = 1 mm avec le titre, pitch `genre_w` = 4 mm, gap `genre_gap` = 1 mm avec le tab (le bloc de tab recule donc de 6 mm en plus du `title_gap`) ; centerline `gx = colonne_titre_gauche − genre_gap − genre_w/2`, fs = **50 % de la fs du titre**, centrée verticalement sur la grille, entre yamakakko 《》 pivotés à 90° (échappés `\《` en KKML, sinon ce sont des délimiteurs ruby). La colonne titre, elle, reste ancrée à 0,75 cm du bord droit. Mesures recueil 2026-11-25.
- **Tailles calibrées sur le recueil (2026-11-24)** : `spec.title_fs = spec.title_spacing = 17,5` pt (fs @choshi = fs titre ; le bloc titre てぃんさぐぬ花 fait 4,3 cm de haut hors ruby pour 7 caractères) ; `spec.page_no_fs = 10` (n° ≈ 2,5 mm de haut) ; syllabes `::vocal` : fs = `int(0,8 × marker_w)` (grand kana ≈ 80 % de la largeur du marker) ; `spec.fs = 12` (kanji kandokoro : encre ≈ 31 px = 11,1 pt sur les scans → em ≈ 12 ; deux kanji en straddle = 24 pt ≤ cell_w 23,3 pt, plus de chevauchement) ; paroles `lyr_fs = spec.lyr_fs = 10,8` pt absolu (`int()` → 10 ; encre ≈ 28 px = 10 pt sur scans).
- **Repli des paroles** (`_cap_lyr_column` + `_lyr_line_segments`) : la hauteur de page étant imposée, une ligne de couplet plus longue que la grille (hauteur de page imposée) est découpée en sous-lignes de ≤ `max_lyr_u` unités (1 unité = 1 pas `lyr_sp` = 1,2 × fs paroles, en GLYPHES AFFICHÉS : les annotations 《…》 ne consomment pas d'unités) ; une ligne trop longue est coupée au caractère UNIQUEMENT entre segments atomiques — un groupe `｛base｝《ruby》` ou une base suivie de son `《ruby》` n'est JAMAIS coupé (une coupe y faisait fuiter les délimiteurs dans le SVG et crasher `_parse_ruby`) ; les sous-lignes de CONTINUATION issues du découpage d'une ligne MARQUEUR s'alignent à la position 3 (en-tête toujours 3 caractères pleine chasse ; règle uniforme, cf. `_verse_indent_target` ; ex. だんじゅかりゆし couplet 1 : 一、 = 2 unités, だんじゅ… à l'unité 3 → la sous-ligne de continuation ぇる… démarre à l'unité 3, même niveau que だん ; 十九の春 : 女、 → 3, 男女、 → 3) — la première sous-ligne garde l'indent de la ligne d'origine (marqueur en haut = 行頭 = 0) ; une ligne sans marqueur repliée garde son indent pour toutes ses sous-lignes. L'avancement du rendu utilise la valeur de retour de la fonction de rendu + UN gap de ligne (l'ancien `cy += len(ln)·sp` brut double-comptait les annotations et faisait déborder les lignes rubyées). Les syllabes empilées d'un `::vocal` peuvent chevaucher la bordure inférieure de la dernière case (conception, reste dans la marge basse de la page). **Kinsoku JLREQ au point de coupe** (`_kinsoku_adjust_cut`, [JLREQ W3C](https://www.w3.org/TR/jlreq/) annexe A ; `@kinsoku simple|strict|off` + `--kinsoku`, défaut `simple` hors `nomura`) : un caractère interdit en tête de ligne (行頭禁則 = haut de la pile en vertical : fermetures, ponctuation 、。，．・：；, 々〻, ー, petits kana ; + ！？ en `strict`) descend en fin de ligne courante (行末 = bas, 追い出し : la ligne courante s'allonge d'une unité au-delà du plafond), et une ouvrante (行末禁則 cl-01) passe en tête de la sous-ligne suivante. NB : ce n'est PAS le ぶら下げ組 de JLreq (suspension de cl-06/cl-07 hors du hanmen en fin de ligne, sans consommer d'unité) — non implémenté ; `off` = coupe au caractère (comportement historique). Concerne uniquement `::lyrics` : `::tab`/`::vocal` ne sont jamais coupés au caractère.
- **Textes verticaux en blocs groupés** : comme dans le layout vertical, tous les textes verticaux du chindami (titre, accordage, lignes de paroles) sont rendus par `_vertical_grouped_text` — base en UN SEUL élément `<text>` (listes `x=`/`y=` répétées), chaque ruby dans son propre bloc à droite de sa base, caractères pivotés (`ー`, parenthèses…) en `<text>` individuels avec `transform="rotate(90 …)"`. La géométrie est celle du plan partagé `_plan_vertical_ruby` (écartement générique des groupes rubyés), identique au rendu per-caractère : le swap est invisible dans le rendu, seule la structure SVG change (blocs copiables d'une pièce).
- **Sauts de page** : les colonnes de paroles remplissent d'abord l'espace libre à GAUCHE des piles de la dernière page de musique (contrainte `L + P + colonne titre + 12 ≤ largeur utile`), l'excédent passe sur des **pages dédiées paroles** de `per_lyr_page` colonnes. Jamais de débordement hors page, jamais de pile perdue.
- **Couleur et filets** : une seule couleur, le noir `#000000` (`cell_color`/`arrow_color`), filets fins `0,4 pt` (`cell_width`/`arrow_width`, essai 2026-11-25 ; cercles de 尺 à `@circle_width 0,5`) ; flèches de répétition instrumentales **pleines** (`rep_fill = True`) : seule la tête (triangle/disque) est remplie, la queue en L porte `fill="none"` (un path ouvert serait sinon fermé implicitement au remplissage → triangle rectangle rempli au coude), disques de répétition vocale **creux** (`vrep_fill = False`) ; la colonne marker est **cosubstantielle** au layout (toujours affichée, même avec `@marker off`).
- **Numéro de page** : `–n–` centré en x (`x = page_w / 2`), **baseline à 0,7 cm du bord inférieur de la feuille**, fs 10, noir ; n = `@page_base` (défaut 1) + index de page.

### Mise en page pour tutoriel vidéo (`@layout tuto`)

Schéma coté : [svg-layout-tuto.svg](svg/svg-layout-tuto.svg).

Le layout `tuto` produit des tablatures destinées aux vidéos tutorielles, sur l'exemple de
https://www.youtube.com/watch?v=GvcZoeCbIPQ (calibré sur la vidéo : **8 cases par dan**, **7 dans par bloc** (bloc unique)).

- Format horizontal : lecture de gauche à droite et de haut en bas (comme `@layout horizontal`).
- Canvas de taille fixe en pixels, pilotée par `@tuto_block LxH` (défaut `1280x720`) : chaque page SVG fait exactement `LxH`.
- Marges : 16 px en haut/gauche/bas, **16 + 1/4 de case à droite** (les vocals sous le straddle de la dernière colonne ne touchent pas la bordure du SVG).
- `@cells_per_dan` / `-c` = cases par dan (défaut 8 en tuto, 12 sinon) ; `@dans_per_page` (**déprécié**) / `-p` = simple plafond de dans par page (défaut = capacité du bloc : 7 en tuto).
- **Page 1 à part** : titre, tempo, accordage, auteur/compositeur/etc. centrés seuls sur la page ; le tempo `@speed` y est rendu `♩=120` en horizontal, sous le titre, centré, au-dessus de `@choshi`, même fs (px) que la ligne `@choshi` (25 px à 1280x720) ; tous les espacements entre blocs de la page de titre sont uniformes : `md_spacing` = 43,2 px (H×0,06 à H=720)
- Pages suivantes : la tablature, découpée en pages de `dans_per_block` dans max (bloc unique en tuto), **pleine largeur** (pas de bande marker en tuto : les flèches de répétition ↓/↑ ne sont pas rendues). Placement des syllabes `::vocal` dans leur case :
- une seule syllabe, pas de point `.` : **sous la note principale** (centre de la case, x = cx), en bas de case ;
- deux syllabes, pas de point (ex. `ぐさ`) : la 1re sous la note principale (x = cx), la 2e sous le straddle (bordure droite). Le découpage en syllabes rattache les petits kana et `ー` à la syllabe précédente (`ちゅ` = 1 syllabe, `やっく` = やっ+く, `まーし` = まー+し) — valable aussi en uchinaguchi/langues ryukyu ;
- token avec point(s) (subdivision) : les éléments (points `・` et syllabes, même couleur que le texte des vocals) sont répartis **en bas de case**, toujours alignés sur la ligne des vocals ;
  pour n éléments, position i = `cx + cell_w * i/n` : i=0 sous la note principale ; n=2 -> cx + bordure (straddle) ; n=3 (grille 3 unités/case des imports Portama) -> cx, cx+cw/3, cx+2cw/3 ; n=4 -> cx, cx+cw/4, cx+cw/2 (straddle), cx+3cw/4 (mi-chemin vers la case suivante) ;

- En layout horizontal (`horizontal`, `tuto`), la note à cheval d'une croche `A/B` est **centrée sur la bordure droite** (verticale) de la case (l'ornement suit), et les deux notes d'un shuffle `A:B` sont côte à côte ; en vertical, le straddle chevauche la bordure inférieure (`render_cell(..., orient="h")` vs `"v"`).
- Le bloc `::lyrics` n'est **pas** rendu en tuto.
- Sortie multipage : `fichier-1.svg` (titre), `fichier-2.svg`… (tablature).

### Mise en page mega (`@layout mega`)

Schéma coté : [svg-layout-mega.svg](svg/svg-layout-mega.svg).

Le layout `mega` produit une page **A3 paysage (42 × 29,7 cm)** contenant **deux blocs horizontaux empilés**, chacun tenant jusqu'à **32 blocs verticaux (dans) de 12 cases** — soit **64 dans (768 cases) par page** (`page_dans_cap` dérivée = `blocks` × `dans_per_block` = 2 × 32). **Ordre de lecture** : bloc horizontal du haut d'abord, de haut en bas et de droite à gauche dans chaque dan, puis bloc horizontal du bas idem.

- Constantes : `spec.page_w = 42 cm`, `spec.page_h = 29,7 cm`, `spec.cells_per_dan = 12`, `spec.dans_per_block = 32`, `spec.blocks = 2`, `spec.margin_l = 40 pt` (~5% de la page, calage PJ), `spec.block_gap = 30 pt` (~1 case, gap entre les deux blocs, qui accueille les noms de chansons), `spec.lyr_inline_max_ratio = 0,15` (seuil des paroles en 1re page, voir ci-dessous).
- Géométrie dérivée de la page : `cell_h = (page_h − 2 × marge − gap) / (2 × 12)` ; `cell_w = largeur restante / (32 × 1,5)` avec marker, sinon `largeur restante / 32` ; `fs = 0,38 × cell_h`.
- **Colonne marker d'une demi-case** (`marker_w = cell_w / 2`) à droite de chaque dan, comme en vertical ; forcée si `::vocal` est présent, sinon pilotée par `@marker` (défaut `on`). Flèches de répétition et syllabes vocales dans la colonne marker (rendu repris de `_draw_vertical_tab`).
- **Titre global** (`@title`, ex. le nom du medley) en **colonne verticale en haut à droite, à droite de tous les blocs (dans la marge droite)** ; genre/auteur en dessous, répétés sur chaque page ; **accordage `@choshi` en bas de la colonne**, bas ancré sur le bas du 2e bloc (`grid_bottom − 4 − len·tuning_spacing`), répété sur chaque page (tablature et paroles). L'espace de cette colonne (`title_offset`) est exclu de la largeur de la grille.
- **Tempo** `@speed` : `♩=120` horizontal (fs 12), `text-anchor="middle"` sur la centerline de base du titre (hors ruby), sous le titre dans la colonne titre, au-dessus de genre/auteur et de `@choshi` ; répété sur chaque page (tablature et paroles)
- `md_spacing = 15` pt — avance uniforme avant chaque bloc de la colonne méta (titre → tempo/genre/auteur, puis entre eux ; `@choshi` ancré en bas du 2e bloc, exclu)
- **Medley** : chaque chanson = une section (`::part <nom>` + `::tab`), plusieurs chansons compilées sur une même page (jusqu'à 64 dans). Le **nom de chaque chanson est imprimé en horizontal (11 pt) au-dessus des colonnes concernées** — centré sur l'étendue des dans de la chanson dans chaque bloc (une chanson qui traverse la césure entre les deux blocs est nommée au-dessus de ses colonnes dans chaque bloc). Le nom **supporte le ruby** (syntaxe 《》 et ｛｝《》, rendu horizontal, ruby au-dessus de la base ; la largeur des flèches d'association suit le plan ruby réel). La **dernière colonne de chaque chanson est complétée par des cases vides** (pas de tenuto) pour que la chanson suivante commence sur une colonne suivante ; si `::vocal` est présent, les syllabes de la colonne sont complétées par des vides (`-`).
- **Paroles** : la 1re page est **réservée aux deux blocs de tablature, pleine largeur**. Les paroles (`::lyrics`) n'y restent que si elles sont très compactes : largeur réservée ≤ `spec.lyr_inline_max_ratio` (15 %) de la largeur utile de la grille ; dans ce cas elles sont rendues en lignes verticales (行) à gauche de la 1re page (une colonne par position x) (largeur réservée sur toutes les pages pour garder une géométrie constante). Sinon elles sont **paginées sur des pages A3 dédiées après les pages de tablature** (`fichier-N+1.svg`…), avec **la même structure de blocs que la tablature** : deux blocs horizontaux empilés de hauteur `spec.cells_per_dan × cell_h` séparés par `spec.block_gap`, couplets en lignes verticales (行) de droite à gauche (avance de ligne horizontale), **repli obligatoire en sous-lignes à la hauteur du bloc** (hauteur réelle par caractère, ruby comprise via `_vertical_text_height`) ; les fragments de repli s'indentent **à la position 3** (en-têtes toujours 3 caractères pleine chasse, règle uniforme ; ex. 十九の春 女、→ 3 et 男女、→ 3) ; l'indent des lignes de continuation (après `|`) suit `_verse_indent_target` (= max(3, plus long marqueur)), **saut d'une ligne vide entre les couplets de deux chansons**, **titre de chaque chanson en ligne verticale 「…」 en gras DEVANT ses paroles** (ligne la plus à droite du run de la chanson = première lue, sens de lecture droite → gauche ; plus grand que le texte des couplets (fs 11, taille des en-têtes de tablature), remonté au haut de bloc : 「 au niveau du premier caractère des lignes (haut de bloc = 行頭), texte une position en dessous, 」 sous le dernier (guillemets pivotés 90° par `_vertical_char`, ruby du titre conservé, fs réduite si le titre dépasse la hauteur du bloc) — ce titre vertical remplace l'ancien chapeau horizontal (nom + flèches). Bloc du haut consommé → bloc du bas ; les deux consommés → page suivante. Colonne titre verticale répétée.
- Pagination automatique multipage : 64 dans par page A3 (`fichier-1.svg`, `fichier-2.svg`…) ; `@dans_per_page` (**déprécié**) / `-p N` réduit ce plafond (de la capacité dérivée `page_dans_cap` = 64). Les dans ne sont jamais coupés entre deux blocs.
- **Numéro de page** : `–n–` centré, à mi-distance entre le bas du 2e bloc de tablature et le bord bas de la feuille ; même hauteur sur une page ne contenant que des paroles ; n = `@page_base` (défaut 1) + index de page.
- Sortie imprimable : `width="42cm" height="29.7cm"`, viewBox en pt, dpi Inkscape 600 (comme `nomura`).
