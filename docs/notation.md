# Notation musicale kunkunshi

## Caractères de position

Les caractères de position (勘所, kandokoro) représentent les positions sur le manche du sanshin. Les 14 positions de base, dans l'ordre croissant des hauteurs :

合 乙 老 四 上 中 尺 工 五 六 七 八 九 十

Par corde : 合 乙 老 (男絃, corde grave), 四 上 中 尺 (中絃, corde moyenne), 工 五 六 七 八 九 十 (女絃, corde aiguë). En hauteurs absolues dans le cas d'un accordage 本調子 avec hauteur de base accordée à do : 合=do, 乙=ré, 老=mi, 四=fa, 上=sol, 中=la, 尺=si♭, 工=do, 五=ré, 六=mi, 七=fa, 八=sol, 九=la, 十=si♭.

Le caractère 下 n'est pas une position autonome : c'est un préfixe de demi-ton, quasi-équivalent du dièse ♯, combiné à un caractère de base. 下老 (シタロウ) = demi-ton au-dessus de 老 ; 下尺 = demi-ton au-dessus de 尺. Les sources traditionnelles (école 野村流) traitent 下老 et 下尺 comme des 勘所 à part entière, avec lectures et doigtés propres ; la pratique moderne écrit aussi 尺♯ pour 下尺 (d'où l'option `@shaku_sharp`). Terminologie retenue dans ce projet : « position de base » pour les 14 caractères ci-dessus, « préfixe » pour 下 (demi-ton), イ (octave supérieure) et ロ (même hauteur, autre corde).

### Positions étendues

| Token | Rendu | Note |
|-------|-------|------|
| 尺 | 尺 | Rendu standard |
| 尺♯ | 尺 (défaut) ou 尺♯ si @shaku_sharp on | Jamais entouré d'un cercle |
| 下尺 | 尺 entouré d'un cercle | Toujours entouré, quelle que soit l'option @shaku_circled |
| 下老 | 下 + 老 condensés en demi-largeur | Un seul `<text>` avec `textLength` à 100% de la largeur d'un kanji et `lengthAdjust="spacingAndGlyphs"`, pour tenir dans une case |
| イ下尺 | Position haute イ + 下尺 | Les 3 caractères イ下尺 condensés, `textLength` à 180% de la largeur d'un kanji, sans cercle autour du 尺 (décision du 16 sept. 2026). Composant large mais nécessaire pour Hiyamikachibushi et autres |

### Positions hautes (préfixes イ / ロ)

Deux systèmes de préfixes indiquent des positions hautes sur le manche. Le préfixe katakana est accolé directement au kanji de position (token à deux caractères).

| Préfixe | Radical | Signification | Lecture |
|---------|---------|---------------|---------|
| イ | 人偏 (亻) | 1 octave au-dessus du kanji de droite | i- (い) |
| ロ | 口偏 (口) | Même hauteur que le kanji de droite, joué sur une autre corde | ro- (ろ) |

Tokens valides avec イ (1 octave au-dessus) :

2 caractères (préfixe + kanji) :

| Token | Lecture | Position |
|-------|---------|----------|
| イ合 | i-ai | 1 octave au-dessus de 合 (corde grave) |
| イ乙 | i-otsu | 1 octave au-dessus de 乙 |
| イ老 | i-rō | 1 octave au-dessus de 老 |
| イ四 | i-yon | 1 octave au-dessus de 四 |
| イ上 | i-jō | 1 octave au-dessus de 上 |
| イ中 | i-naka | 1 octave au-dessus de 中 ; en pratique souvent remplacé par 九 |
| イ尺 | i-shaku | 1 octave au-dessus de 尺 |
| イ工 | i-kō | 1 octave au-dessus de 工 (corde aiguë) |
| イ五 | i-go | 1 octave au-dessus de 五 |

3 caractères (préfixe + 下 + kanji) :

| Token | Lecture | Position |
|-------|---------|----------|
| イ下老 | i-shita-rō | 1 octave au-dessus de 下老 |
| イ下尺 | i-shita-shaku | 1 octave au-dessus de 下尺 |

Tokens valides avec ロ (même hauteur, autre corde) :

| Token | Lecture | Position |
|-------|---------|----------|
| ロ上 | ro-jō | Même hauteur que 上, autre corde |
| ロ中 | ro-naka | Même hauteur que 中, autre corde |
| ロ尺 | ro-shaku | Même hauteur que 尺, autre corde |
| ロ五 | ro-go | Même hauteur que 五, autre corde |

Positions ロ rares dans la pratique : ロ尺 et ロ五 n'apparaissent que selon les pièces ; ロ上 est utile dans les pièces jouées en position moyenne du manche (中位), où il remplace 上 sans déplacer la main gauche. Seules ces quatre formes sont attestées en usage ; d'autres composites à radical 口 existent en Unicode (呬 = ロ四, 哈 = ロ合, 咾 = ロ老, 𠮟 = ロ七, 叭 = ロ八, 㕤 = ロ九, 叿 = ロ工) sans attestation d'usage réel. La lecture du préfixe varie selon l'école : ro- (ろじょう) ou kō- (野村流 : こうご, こうしゃく).

### Positions hautes + 下尺 (イ下尺, ロ下尺)

Le préfixe peut aussi s'appliquer à 下尺. Le token fait 3 caractères (イ下尺 ou ロ下尺). Rendu : les 3 caractères condensés via `textLength` à 180% de la largeur d'un kanji avec `lengthAdjust="spacingAndGlyphs"`. Le 尺 n'est PAS entouré d'un cercle dans ce composé (décision du 16 sept. 2026) : le 下 reste visible et le rendu suit le patron de 下老 élargi à 3 caractères. Le composant est large mais nécessaire (Hiyamikachibushi).

Rendu : préfixe et kanji condensés via un seul `<text>` avec `textLength` et `lengthAdjust="spacingAndGlyphs"`. 2 caractères → 120% de fs, 3 caractères (イ下尺) → 180% de fs. Les suffixes de technique s'appliquent (ex : イ尺* = イ尺 + uchi-utu) et sont positionnés par rapport au bord du texte. Pour イ下尺 / ロ下尺, pas de cercle : les 3 caractères sont rendus condensés (le 下 reste visible).

Note historique : イ est un raccourci du radical 人偏 (亻), forme gauche du kanji 人. ロ est un raccourci du radical 口偏 (口). La plupart des composites n'ont pas de caractère Unicode dédié (伍 = 亻+五 est une exception), d'où l'usage des préfixes katakana dans le KKML.

### Caractères vocaux (non rendus sur le sanshin)

才 (sai) = sol, 凡 (bon) = la, 勺 (shaku) = si — n'apparaissent que dans la transcription vocale.

## Tokens spéciaux

- `◯` — repos (cercle). Variantes tolérées en KKML : ◯, ○, 〇, O, o, 0 — toutes normalisées en ◯ à l'analyse
- `-` — case vide (EMPTY_TOKEN), rien n'est rendu. Note : `四-五` (avec `-` entre deux notes) est un accord, pas une case vide — le `-` seul est le token vide.
- `|:` — début de boucle. Peut être utilisé comme token autonome ou préfixé à une note (`|:工`). Une flèche vectorielle descendante est rendue dans la colonne marker à droite de la case : trait horizontal depuis la bordure gauche, trait vertical descendant, triangle creux pointant vers le bas.
- `:|` — fin de boucle. Peut être utilisé comme token autonome ou suffixé à une note (`尺:|`). Une flèche vectorielle montante est rendue dans la colonne marker à droite de la case : trait horizontal depuis la bordure gauche, trait vertical montant, triangle creux pointant vers le haut.

Les boucles de répétition (`|:` … `:|`) ne sont pas limitées au début d'une chanson (le terme « intro » est trompeur). Elles peuvent apparaître à n'importe quel endroit, et une chanson peut en contenir plusieurs. Aucun cas de boucles imbriquées n'a été observé.

## Syllabes vocales

Les syllabes vocales sont placées dans la colonne marker (à droite de chaque pile de cases) pour indiquer le placement des syllabes du chant sur le rythme. Règle : 1 token (séparé par des espaces) = 1 syllabe. Un token peut faire plusieurs caractères (consonnes complexes de l'uchi-na-guchi, voyelles longues). Au moins 4 syllabes par case sont acceptées, et les syllabes peuvent chevaucher la bordure inférieure.

### Tokens multi-caractères (うちなぐち)

Certaines consonnes de l'okinawaïen s'écrivent sur deux caractères : un caractère principal plein + un petit kana combinant. Ces tokens forment UNE seule syllabe et s'écrivent sans espace entre les caractères :

| Token | Lecture | Structure |
|-------|---------|-----------|
| ぐゎ | gwa | ぐ + petit ゎ |
| くゎ | kwa | く + petit ゎ |
| てぃ | ti | て + petit ぃ |
| でぃ | di | で + petit ぃ |
| とぅ | tu | と + petit ぅ |
| どぅ | du | ど + petit ぅ |
| づぅ | dū | づ + petit ぅ |
| ふぁ | fa | ふ + petit ぁ |
| ふぃ | fi | ふ + petit ぃ |
| よー | yō | よ + ー (voyelle longue) |

Petits kana combinants reconnus : ぁぃぅぇぉゃゅょゎ (hiragana) et ァィゥェォャュョヮ (katakana), plus ー (chōonpu, voyelle longue).

Rendu vertical : le caractère principal est aligné sur la note ; les caractères combinants sont empilés en dessous, espacés de `syllable_fs * 0.85`. Les petits kana sont rendus à la même taille de police (leur glyphe est naturellement plus petit). Le ー (chōonpu) est pivoté de 90° pour devenir un trait vertical, comme en typographie japonaise verticale. Le chevauchement de la bordure inférieure de la case est accepté.

### Positionnement

- Taille de police : SYLLABLE_FS = min(int(cell_h * 0.35), int(marker_w * 0.8)) ≈ 20px avec les valeurs par défaut (cell_w=52, cell_h=58, marker_w=26)
- Le caractère principal de chaque syllabe est positionné à la même hauteur verticale que la note correspondante
- Position x : centre de la colonne marker = `x + cell_w + marker_w / 2`
- Position y : `cy + cell_h / 2 + syllable_fs / 3` (centré verticalement sur la note)
- Couleur : gris foncé (#333)
- Police : serif (même que les notes)

### Syntaxe KKML

```kkml
::tab
中 中 中 中
工 工 工 工
::

::vocal
てぃん さ ぐゎ ぬ
は な や ー
::
```

Chaque ligne dans un bloc `::vocal` correspond à la ligne de `::tab` de même index. Les syllabes sont séparées par des espaces ; les caractères d'une même syllabe sont accolés (sans espace). Le bloc `::vocal` doit suivre immédiatement un bloc `::tab` pour être associé correctement.

### Alignement ligne par ligne

- La syllabe i de la ligne vocale j s'aligne sur la note i de la ligne de tablature j
- Si une ligne vocale a moins de syllabes que la ligne de tab (ex. notes d'intro uta-mochi sans chant), le reste est complété par des vides (`-`) : l'alignement des lignes suivantes est préservé
- Si une ligne vocale a plus de syllabes que la ligne de tab, l'excédent est ignoré

### Comportement

- Si `@marker` est désactivé mais qu'un bloc `::vocal` existe, la colonne marker est automatiquement activée
- Les syllabes vides (`-`) ne sont pas rendues
- Jusqu'à 4 syllabes ou plus peuvent être empilées verticalement dans une seule case

## Modes rythmiques

Le format d'un token encode son rythme :

### Noire (note simple)
- Format : un seul caractère (ex : `中`)
- Rendu : caractère plein taille, parfaitement centré dans la case

### Croche (A/B)
- Format : `合/工` (séparateur `/`)
- Rendu : note principale `合` centrée en pleine taille (comme une noire) + note secondaire `工` plus petite (62% de la taille), positionnée sur le bord inférieur de la case (à cheval entre la case courante et la case du dessous)
- La note principale est le premier temps, la note à cheval est le deuxième temps de la croche

### Shuffle 早弾き (A:B)
- Format : `合:工` (séparateur `:`)
- Rendu : deux notes égales empilées verticalement, taille 72% de la noire
- La note supérieure est au-dessus du centre, la note inférieure en dessous

### Ornement (multi-caractères)
- Format : plusieurs caractères sans séparateur (ex : `合工尺`)
- Rendu : caractères empilés verticalement, taille 72%, centrés sur l'axe vertical de la case

### Accord (notes simultanées)
- Format : `四-五` ou `合-工-尺` (séparateur `-`)
- Rendu : identique à l'ornement (empilé vertical à 72%), mais sémantiquement différent (notes simultanées)
- Maximum 3 notes (le sanshin n'a que 3 cordes)
- Cas d'usage : Hiyamikachibushi (accords Yon-Go)

### Positions hautes 3-caractères

| Token | Lecture | Rendu |
|-------|---------|-------|
| イ下尺 | i-shita-shaku | イ下尺 condensés (3 caractères), textLength 180% de fs, sans cercle |

Large mais fonctionnel. Le code traite ce cas dans une branche dédiée (3 caractères, `base_tok[1:] == "下尺"`).

## Suffixes de technique (souhou)

Apposés après le caractère de position dans le token KKML. Peuvent se combiner (ex : `中s*` = jeu faible + hammer-on).

| Suffixe | Nom | Rendu SVG | Description |
|---------|-----|-----------|-------------|
| `*` | uchi-utu (打音) | caractère ｀ (accent grave) en haut-droite, même police et taille que la note | Presser la corde sans gratter (hammer-on) |
| `^` | kaki-utu (掛音) | ┗ (U+2517) roté 180° en haut-droite | Upstroke (gratter de bas en haut avec l'ongle) |
| `v` | aki-utu (開音) | V en bas-gauche, même police et taille que la note | Relâcher le doigt (pull-off) |
| `<` | kachi-utu (掻音) | ┗ en bas-gauche, même police et taille que la note | Gratter la corde avec la main gauche |
| `s` | kuubanchi (小弾) | kanji rendu à 67% de la taille (−33%), centrage inchangé | Jeu faible |
| `=` | taachi (二弾) | trait vertical à droite du kanji | Jouer 2 ou 3 cordes simultanément |

Les marques diacritiques (`*`, `^`, `v`, `<`) sont rendues dans la même police (serif) et la même taille que la note (`int(fs * 1.1)`, +10%). Règle de positionnement : l'encre visible du signe ne doit pas chevaucher l'encre visible de la note. Chaque signe a ses propres offsets (dx, dy) dans `TECHNIQUE_SUFFIXES` :

- uchi-utu (`｀`) : `dx=0.22`, `dy=0.05` (en haut-droite)
- kaki-utu (`┗` roté 180°, échelle 0.75) : `dx=0.28`, `dy=-0.22` (en haut-droite, barre supérieure au-dessus de la note)
- aki-utu (`V`) : `dx=0.45`, `dy=0.15` (en bas-gauche)
- kachi-utu (`┗`) : `dx=0.45`, `dy=0.15` (en bas-gauche)

Les offsets sont des multiplicateurs de `fs` : `tx = cx ± fs * dx`, `ty = cy + 7 + fs * dy`. Aucun souhou ne modifie les coordonnées de la note, sauf `s` qui réduit la taille à 67% sans déplacer le centre.

## Options d'en-tête KKML

| Métadonnée | Défaut | Effet |
|------------|--------|-------|
| `@shaku_circled on` | off | Rend tous les 尺 en 尺 entourés d'un cercle, y compris 尺 dans les croches (note principale ou note à cheval). 尺♯ et 下尺 ne sont pas affectés (下尺 est toujours entouré). |
| `@shaku_sharp on` | off | Rend les 尺♯ explicitement avec le symbole ♯. Sinon, 尺♯ est rendu comme 尺. |

## Détails de rendu (fonction render_cell)

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
