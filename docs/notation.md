# Notation musicale 工工四 (kunkunshi)

## Le sanshin et la tablature 工工四

Le [sanshin (三線)](https://fr.wikipedia.org/wiki/Sanshin) est un luth à trois cordes originaire d'Okinawa, dérivé du sanxian chinois importé au royaume de Ryūkyū aux XIVe-XVe siècles. Il comprend un long manche sans frettes et une caisse en peau de python. Il est joué avec un plectre en corne de buffle (爪, tsumé). Instrument central de la musique classique Ryukyu (琉球古典), du folklore Ryukyu (琉球民謡) et de la danse, il est l'ancêtre du [shamisen](https://fr.wikipedia.org/wiki/Shamisen), introduit à Osaka au XVIe siècle depuis le port de Sakai.

Comme le manche est sans frettes, la musique ne se note pas en hauteurs absolues mais en positions de doigts : c'est le [工工四 (kunkunshi)](https://ja.wikipedia.org/wiki/工工四), système de tablatures créé au XVIIIe siècle par [屋嘉比朝寄 (Yakabi Chōki)](https://ja.wikipedia.org/wiki/屋嘉比朝寄), qui a adapté la notation chinoise [工尺譜 (gongchepu)](https://fr.wikipedia.org/wiki/Gongchepu) en caractères représentant des positions sur le manche du sanshin, ou 勘所 (kandokoro). Chaque caractère indique où poser le doigt, et non pas quelle note sonnera — comme une tablature de guitare. Les trois cordes sont accordées différemment selon les 調子 (chōshi, accordages), le système de notation s'appliquant à n'importe quel accordage. La transmission s'est longtemps faite oralement ; le kunkunshi imprimé, normalisé par l'école Nomura-ryū (野村流) au XIXe siècle, reste aujourd'hui le support standard de l'enseignement.

## Positions de base

Les caractères de position (勘所, kandokoro) représentent les positions sur le manche du sanshin. Les 14 positions de base, dans l'ordre croissant des hauteurs, sont :

合 乙 老 四 上 中 尺 工 五 六 七 八 九 十

Lectures usuelles, hauteurs (demi-tons au-dessus de 合 en accordage 本調子) et doigtés :

| Position | Lecture | Hauteur (demi-tons) | Doigt | Variante |
|----------|---------|---------------------|-------|----------|
| 合       | あい (ai) | 0 | 開弦 (corde à vide) | |
| 乙       | おつ (otsu) | +2 | ㊀ 人差指 (index) | |
| 老       | ろう (rō) | +4 | ㊁ 中指 (majeur) | |
| 四       | よん (yon) | +5 | 開弦 (corde à vide) | |
| 上       | じょう (jō) | +7 | ㊀ 人差指 (index) | |
| 中       | なか (naka) | +9 | ㊁ 中指 (majeur) | Appelé ちゅう (chū) par certaines écoles et dans certains manuels récents |
| 尺       | しゃく (shaku) | +10 | ㊃ 小指 (auriculaire)* | |
| 工       | こう (kō) | +12 | 開弦 (corde à vide) | |
| 五       | ご (go) | +14 | ㊀ 人差指 (index) | |
| 六       | ろく (roku) | +16 | ㊁ 中指 (majeur) | |
| 七       | しち (shichi) | +17 | ㊃ 小指 (auriculaire)* | |
| 八       | はち (hachi) | +19 | ㊃ 小指 (auriculaire)* | |
| 九       | きゅう (kyū) | +21 | ㊃ 小指 (auriculaire)* | |
| 十       | じゅう (jyū) | +22 | ㊃ 小指 (auriculaire)* | |

\* Doigtés des positions au-delà du majeur à confirmer : selon les écoles et la position de la main (上部/中部), 尺 et 七 peuvent se jouer index ou majeur (traité 野村流, position médiane : 老中六 index, 尺七 majeur, 八九 auriculaire). Les cordes à vide (合四工) et les doigtés index/majeur sont établis.

Notation 野村流 des doigtés (指位記号) : les kanji numéraux encerclés sont utilisés dans la marge gauche des kunkunshi 野村流 pour indiquer le doigté et les changements de position de la main gauche — ㊀ (一) = 人差指 (index), ㊁ (二) = 中指 (majeur), ㊂ (三) = 無名指 (annulaire), ㊃ (四) = 小指 (auriculaire). Bloc Unicode U+3280–U+3283 (Enclosed CJK Letters and Months), la série complète allant jusqu'à ㊉ (十). NB kkml2svg : ces caractères ne doivent PAS apparaître comme tokens de position — les REST_VARIANTS du tokenizer normalisent les caractères encerclés vers le silence ◯, ce qui les rendrait ambiguës dans la grille.

Wikipédia JA signale des variations de lecture selon la région et l'école. Aucun impact en KKML : les kanji sont identiques quelle que soit la lecture.

Répartition par corde :

| Corde   | Nom de corde | Positions | Hauteurs (本調子, base do) |
|---------|-----|-----------|----------------------------|
| Grave   | 男絃 ou 男ジル (uojiru) | 合 乙 老 | do, ré, mi |
| Médiane | 中絃 ou 中ジル (nakajiru) | 四 上 中 尺 | fa, sol, la, si♭ |
| Aiguë   | 女絃 ou 女ジル (miijiru) | 工 五 六 七 八 九 十 | do, ré, mi, fa, sol, la, si♭ |

Le caractère 下 n'est pas une position autonome : c'est un préfixe de demi-ton, quasi-équivalent du dièse ♯, combiné à un caractère de base. 下老 (シタロウ) = demi-ton au-dessus de 老 ; 下尺 = demi-ton au-dessus de 尺. Exception : 下八, qui n'est pas un demi-ton au-dessus de 八 mais un kandokoro propre — sur la 女絃 (corde aiguë), une case sous 八, doigté annulaire (無名指) selon la table 野村流 (source : 世禮國男, 増訂琉球音樂樂典, p. 14 : octave de 中, alias 仲). Les sources traditionnelles (école 野村流) traitent 下老 et 下尺 comme des 勘所 à part entière, avec lectures et doigtés propres ; la pratique moderne écrit aussi 尺♯ pour 下尺 (d'où l'option `@shaku_sharp`). Terminologie retenue dans ce projet : « position de base » pour les 14 caractères ci-dessus, « préfixe » pour 下 (demi-ton), イ (octave supérieure) et ロ (même hauteur, autre corde).

### Positions étendues

| Token | Lecture | Rendu | Note |
|-------|-------|---|------|
| 下老   | shita-rō | 下 + 老 condensés en demi-largeur | Un seul `<text>` avec `textLength` à 100% de la largeur d'un kanji et `lengthAdjust="spacingAndGlyphs"`, pour tenir dans une case |
| 尺♯   | shaku-sharp | 尺 (défaut) ou 尺♯ si @shaku_sharp on | Jamais entouré d'un cercle |
| 下尺  | shita-shaku | 尺 entouré d'un cercle | Toujours entouré, quelle que soit l'option @shaku_circled |
| イ下尺 | i-shita-shaku | Position haute イ + 下尺 | Les 3 caractères イ下尺 condensés, `textLength` à 180% de la largeur d'un kanji, sans cercle autour du 尺. Composant large mais nécessaire pour Hiyamikachibushi et autres |
| 下八 | shita-hachi |下 + 八 condensés, même patron que 下老 | Sans cercle. Kandokoro propre (女絃 sous 八, octave de 中), pas un demi-ton |

### Positions hautes (préfixes イ et ロ)

Deux systèmes de préfixes indiquent des positions hautes sur le manche. Le préfixe katakana est accolé directement au kanji de position (token à deux caractères).

| Préfixe      | Lecture | Signification | Lecture |
|--------------|---------|------|---------|
| イ | i        |1 octave au-dessus du kanji de droite, joué sur la même corde | i- (い) |
| ロ | ro ou kō | Même hauteur que le kanji de droite mais joué sur une autre corde | ro- (ろ), ou kō- (こう) selon l'école |

Tokens valides avec イ (1 octave au-dessus) :

2 caractères (préfixe + kanji) :

| Token | Lecture | Position |
|-------|---------|----------|
| イ合 | i-ai | 1 octave au-dessus de 合 |
| イ乙 | i-otsu | 1 octave au-dessus de 乙 |
| イ老 | i-rō | 1 octave au-dessus de 老 |
| イ四 | i-yon | 1 octave au-dessus de 四 |
| イ上 | i-jō | 1 octave au-dessus de 上 |
| イ中 | i-naka | 1 octave au-dessus de 中 ; en pratique souvent remplacé par 九 |
| イ尺 | i-shaku | 1 octave au-dessus de 尺 |
| イ工 | i-kō | 1 octave au-dessus de 工 |
| イ五 | i-go | 1 octave au-dessus de 五 |
| イ六 | i-roku | 1 octave au-dessus de 六 |
| イ七 | i-shichi | 1 octave au-dessus de 七 |

イ六 et イ七 sont rares : attestés comme noms de 勘所 dans la nomenclature 野村流 (nomura-ryū), mais sans occurrence connue dans des kunkunshi réels ; la plupart des ressources ne les emploient pas.

3 caractères (préfixe + 下 + kanji) :

| Token | Lecture       | Position                  |
|-------|---------------|---------------------------|
| イ下老 | i-shita-rō    | 1 octave au-dessus de 下老 |
| イ下尺 | i-shita-shaku | 1 octave au-dessus de 下尺 |

L'existence de イ下八 n'est pas documentée.

Tokens valides avec ロ (même hauteur, autre corde) :

| Token | Lecture | Position |
|-------|---------|----------|
| ロ上 | ro-jō ou kō-jō | Même hauteur que 上 mais joué sur la corde grave |
| ロ中 | ro-naka ou kō-naka | Même hauteur que 中 mais joué sur la corde grave |
| ロ尺 | ro-shaku ou kō-shaku | Même hauteur que 尺 mais joué sur la corde grave |
| ロ五 | ro-go ou kō-go | Même hauteur que 五 mais joué sur la corde médiane |

Les positions ロ sont rares en pratique : ロ尺 et ロ五 n'apparaissent que selon les pièces ; ロ上 est utile dans les pièces jouées en position moyenne du manche (中位), où il remplace 上 sans déplacer la main gauche. Seules ces quatre formes sont attestées en usage. La lecture du préfixe varie selon l'école : ro- ou kō- (野村流, Nomura-ryu).

#### Kanjis composés (pour information — non implémentés)

Certains composites préfixe + kanji existent comme caractères Unicode. Ce sont des caractères chinois/japonais préexistants (souvent rares ou dialectaux), réutilisés graphiquement parce que le radical gauche évoque le préfixe. Le mécanisme lui-même (radical 亻 accolé = octave supérieure) vient du 工尺譜, où le gongchepu cantonais écrit l'octave haute 仩 (上), 伬 (尺), 仜 (工), 伍 (五), 亿 (乙).

Composites 口偏 (Source : inventaire R. López García, email W3C public-music-notation 0005, 2017) :

| Caractère | Équivalent | Attestation d'usage |
|-----------|------------|---------------------|
| 㕶 | ロ五 | Utilisé réellement |
| 呎 | ロ尺 | Utilisé réellement (caractère courant : « pied », unité, en cantonais) |
| 叿 | ロ工 | Non attesté |
| 呬 | ロ四 | Non attesté |
| 哈 | ロ合 | Non attesté |
| 咾 | ロ老 | Non attesté |
| 𠮟 | ロ七 | Non attesté (variante japonaise de 叱) |
| 叭 | ロ八 | Non attesté (courant : 喇叭) |
| 㕤 | ロ九 | Non attesté |

Composites 亻 (série イ) — aucun composite dédié attesté en usage sanshin ; les caractères suivants sont les signes d'octave haute du gongchepu cantonais, ou des caractères courants réutilisables graphiquement :

| Caractère | Équivalent | Attestation d'usage |
|-----------|------------|---------------------|
| 佮 | イ合 | Caractère courant cantonais (« ensemble »), pas attesté comme signe de position |
| 亿 | イ乙 | Gongchepu cantonais ; caractère courant (亿 = simplifié de 億, « cent millions ») |
| 仩 | イ上 | Gongchepu cantonais uniquement |
| 伬 | イ尺 | Gongchepu cantonais uniquement |
| 仜 | イ工 | Gongchepu cantonais uniquement |
| 伍 | イ五 | Gongchepu cantonais ; caractère courant chinois (« compagnie », rang militaire) |

Aucun composite 亻 attesté pour 老, 四, 中, 六, 七, 八, 九, 十.

Statut KKML : non implémentés. À terme, ces caractères seront tolérés comme tokens d'entrée et normalisés vers leur décomposition (呬 → ロ四, 伬 → イ尺, etc.), mais jamais rendus tels quels.

### Cas des positions hautes + 下老 ou 下尺

Le préfixe peut aussi s'appliquer à 下老 et 下尺. Le token fait alors 3 caractères (ex. イ下尺 ou ロ下尺). Rendu : les 3 caractères condensés via `textLength` à 180% de la largeur d'un kanji avec `lengthAdjust="spacingAndGlyphs"`. Le 尺 n'est PAS entouré d'un cercle dans ce composé (décision du 16 sept. 2026) : le 下 reste visible et le rendu suit le patron de 下老 élargi à 3 caractères. Le composant est large mais nécessaire (Hiyamikachibushi).

Rendu : préfixe et kanji condensés via un seul `<text>` avec `textLength` et `lengthAdjust="spacingAndGlyphs"`. 2 caractères → 120% de fs, 3 caractères (イ下尺) → 180% de fs. Les suffixes de technique s'appliquent (ex : イ尺* = イ尺 + uchi-utu) et sont positionnés par rapport au bord du texte. Pour イ下尺 / ロ下尺, pas de cercle : les 3 caractères sont rendus condensés (le 下 reste visible).

Note historique : イ est un raccourci du radical 人偏 (亻), forme gauche du kanji 人. ロ est un raccourci du radical 口偏 (口). Les composites précomposés qui existent en Unicode sont listés plus haut à titre d'information ; le KKML utilise les préfixes katakana (2 caractères) comme forme canonique.

### Caractères vocaux (non rendus sur le sanshin)

才 (sai) = sol, 凡 (bon) = la, 勺 (shaku) = si — n'apparaissent que dans la transcription vocale.

## Tokens spéciaux

- `◯` — repos (cercle). Variantes tolérées en KKML : ◯, ○, 〇, O, o, 0 — toutes normalisées en ◯ à l'analyse
- `-` — case vide (EMPTY_TOKEN), rien n'est rendu. Note : `四-五` (avec `-` entre deux notes) est un accord, pas une case vide — le `-` seul est le token vide.
- `|:` — début de boucle. Peut être utilisé comme token autonome ou préfixé à une note (`|:工`). Une flèche vectorielle descendante est rendue dans la colonne marker à droite de la case : trait horizontal depuis la bordure gauche, trait vertical descendant, triangle creux pointant vers le bas.
- `:|` — fin de boucle. Peut être utilisé comme token autonome ou suffixé à une note (`尺:|`). Une flèche vectorielle montante est rendue dans la colonne marker à droite de la case : trait horizontal depuis la bordure gauche, trait vertical montant, triangle creux pointant vers le haut.

Les boucles de répétition (`|:` … `:|`) ne sont pas limitées au début d'une chanson (le terme « intro » est trompeur). Elles peuvent apparaître à n'importe quel endroit, et une chanson peut en contenir plusieurs. Les boucles ne peuvent pas être imbriquées.

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
中 合-工 尺-中* 上 四 合-老* 四 工
::

::vocal
てぃ ん さ ぐ ぬ は な や ー
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

### Une noire (A)
- Format : un seul caractère (ex : `中`)
- Rendu : caractère plein taille, parfaitement centré dans la case

### Deux croches (A/B)
- Format : `合/工` (séparateur `/`)
- Rendu : note principale `合` centrée en pleine taille (comme une noire) + note secondaire `工` plus petite (62% de la taille), positionnée sur le bord inférieur de la case (à cheval entre la case courante et la case du dessous)
- La note principale est le premier temps, la note à cheval est le deuxième temps de la croche

### Une croche pointée et une double croche (早弾き shuffle) (A:B)
- Format : `合:工` (séparateur `:`)
- Rendu : deux notes égales empilées verticalement, taille 72% de la noire
- La note supérieure est au-dessus du centre, la note inférieure en dessous

### Accord (notes simultanées) (A-B)
- Format : `四-工` ou `合-四-工` (séparateur `-`)
- Rendu : caractères empilés verticalement, taille 72%, centrés sur l'axe vertical de la case
- Maximum 3 notes (le sanshin n'a que 3 cordes)
- Cas d'usage : par exemple dans ヒヤミカチ節 (Hiyamikachibushi) : 四-工 et 合-四-工

### Token non reconnu
- Tout token sans séparateur qui n'est pas une position (simple ou étendue) est non reconnu
- Rendu dégradé : 3 premiers caractères au maximum, condensés en largeur (patron `イ中` pour 2 caractères, `イ下尺` pour 3)
- Alerte sur stderr à la première occurrence de chaque token unique
- Historique : l'ancien « ornement » (empilement vertical de tous les caractères) est déprécié le 19 sept. 2026 — sans sémantique musicale ; les kanji empilés réels sont des croches (`A/B`), du hayabiki (`A:B`) ou des accords (`A-B`)

### Positions hautes 3-caractères

| Token | Lecture | Rendu |
|-------|---------|-------|
| イ下尺 | i-shita-shaku | イ下尺 condensés (3 caractères), textLength 180% de fs, sans cercle |

Large mais fonctionnel. Le code traite ce cas dans une branche dédiée (3 caractères, `base_tok[1:] == "下尺"`).

## Suffixes de technique (走法, souhou)

Apposés après le caractère de position dans le token KKML. Peuvent se combiner (ex : `中s*` = jeu faible + hammer-on).

| Suffixe | Nom | Rendu SVG | Description |
|---------|-----|-----------|-------------|
| `*` | uchi-utu (打音) | caractère ｀ (accent grave) en haut-droite, même police et taille que la note | Presser la corde sans gratter (hammer-on) et tenir la note |
| ? | uchi-nuchi-utu (打抜音) | caractère <à préciser> (apostrophe vide) | Hammer-on sans tenir la note |
| `^` | kaki-utu (掛音) | ┗ (U+2517) pivoté de 180° en haut-droite | Upstroke (gratter de bas en haut avec le bachi) |
| `v` | aki-utu (開音) | V en bas-gauche, même police et taille que la note | Relâcher le doigt (pull-off) |
| `<` | kachi-utu (掻音) | ┗ en bas-gauche, même police et taille que la note | Gratter la corde avec la main gauche |
| `s` | kuubanchi (小弾) | kanji rendu à 67% de la taille (−33%), centrage inchangé | Jeu faible |
| `=` | taachi (二弾) ou tsuiri-bichi (列弾) | trait vertical à droite du kanji | Jouer 2 ou 3 cordes simultanément |

Les marques diacritiques (`*`, `^`, `v`, `<`) sont rendues dans la même police et la même taille que la note (`int(fs * 1.1)`, +10%). Règle de positionnement : l'encre visible du signe ne doit pas chevaucher l'encre visible de la note. Chaque signe a ses propres offsets (dx, dy) dans `TECHNIQUE_SUFFIXES` :

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
