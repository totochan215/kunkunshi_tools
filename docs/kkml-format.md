# Référence du format KKML

Le KKML (Kunkunshi Markup Language) est un format texte destiné à l'encodage des tablatures Kunkunshi. L'objectif est de proposer une alternative au format JSON de Portama, qui réponde aux défis suivants :
- Simple et visuel,
- Facile à saisir à l'aide d'un éditeur de texte,
- Non dépendant de polices spécifiques (une police japonaise compatible UTF-8 suffit),
- Un musicien doit pouvoir exécuter le morceau en ayant le fichier KKML brut (non rendu) sous les yeux.

Par ailleurs, KKML tente de combler des certains manques inhérents au format JSON de Portama : support de positions étendues manquantes, de figures rythmiques non prises en charge, plus grande flexibilité dans le positionnement des syllabes vocales, variété des styles de mise en page, etc.

En développant KKML et ses outils, nous espérons rendre l'édition de tablatures Kunkunshi accessible à tous !

## Format source

KKML se base sur le format texte brut encodé en UTF-8, sans utilisation des extensions PUA (private use area).

## Structure générale

```
# commentaire (ignoré)
@meta valeur
@cells_per_dan 12

::part
contenu
::

::tab
<tablature sous forme de cellules représentant des temps, séparées par des espaces ;
au sein de chaque cellule, figures représentant des notes, leurs altérations et leurs
techniques de jeu. Ajout possible de boucles instrumentales ou vocales.>
::

::vocal
<placement du chant sur les temps de la tablature : découpage en syllabes,
les points `.` et syllabes subdivisent chaque temps en parts égales. Chaque ligne de
::vocal correspond à la ligne de ::tab de même index. Ajout possible de marques de
début et de fin du chant.>
::

::lyrics
<paroles en texte libre organisées par couplets, indépendamment des temps. 
Ruby supporté>
::

```

Le fichier est composé d'un en-tête comportant des métadonnées, et de sections thématiques. L'ordre n'est pas imposé. Les sections ne peuvent pas être imbriquées.

Les lignes précédées du symbole \# (commentaire) sont ignorées.

## Métadonnées

| Clé              | Défaut     | Description                       |
|------------------|------------|-----------------------------------|
| `@format`        | `KKML`     | Format de fichier                 |
| `@version`       | —          | Numéro de version du format       |
| `@title`         | —          | Titre du morceau (ruby supporté)  |
| `@genre`         | —          | Genre musical (ruby supporté)      |
| `@author`        | —          | Auteur du morceau (ruby supporté) |
| `@composer`      | —          | Compositeur (ruby supporté)       |
| `@lyricist`      | —          | Parolier (ruby supporté)          |
| `@origin`        | —          | Origine (ruby supporté)           |
| `@source`        | —          | Source de la version du morceau (recueil chindami, recueil nomura, site web, production personnelle, etc.) — texte libre.|
| `@comment`       | —          | Commentaire — texte libre.        |
| `@choshi`        | `本調子`    | Accordage relatif. Valeurs connues : `本調子`, `二揚げ`, `三下げ`, `一二揚げ`, `一揚げ`. Ancien nom `@tuning` accepté (alias) |
| `@base_note`     | `C3`       | Note de base : hauteur de la position 合 (accordages 本調子, 二揚げ, 三下げ) ou 合 moins 2 demi-tons (一二揚げ, 一揚げ). |
| `@layout`        | `vertical` | Modèle de mise en page : `vertical`, `horizontal`, `nomura`, `chindami`, `tuto` ou `mega` (voir [svg-layout.md](svg-layout.md)) |
| `@dans_per_page` | —          | **Déprécié** — Nombre max de *dans* par page avant un saut de page forcé. La capacité de page est dérivée du layout (`tab_blocks` × `dans_per_block`, propriété `page_dans_cap` du `LayoutSpec`) ; cette méta n'est conservée que comme simple plafond (vertical/tuto/mega), sans effet en nomura/chindami/horizontal (page imposée). Ancien nom `@page_dans` accepté (alias) |
| `@page_base`     | `1`        | Numéro affiché sur la 1ère page (layouts à page fixe `nomura`/`chindami`/`mega`, sous la forme –n– ; les pages suivantes s'incrémentent automatiquement. Entier >= 1 |
| `@tuto_block`    | `1280x720` | Layout `tuto` uniquement : dimensions du bloc en pixels (`LxH`) ; chaque page SVG fait exactement LxH |
| `@mega_dans`     | `32`       | **Déprécié** — Layout `mega` uniquement : ancienne surcharge du nombre de colonnes (*dans*) par bloc horizontal. Remplacé par le champ `dans_per_block` du `LayoutSpec` mega (propriété du bloc fixée par le layout ; 2 blocs/page A3, donc 64 dans/page par défaut, la largeur des cases s'adapte). Conservé comme simple surcharge de la valeur effective en mega |
| `@cells_per_dan` | —          | Nombre de cellules par *dan*. Utilisé par `kkml_clean.py` comme indice de repli pour ::tab et ::vocals. Utilisé par les mises en page `vertical` et `horizontal` (défaut `12`) et `tuto` (défaut `8`), mais pas par `chindami`, `nomura` et `mega`, qui imposent la valeur `12`). `-c n` en CLI. Ancien nom `@cols` accepté mais non canonique. |
| `@marker`        | `on`       | Active/désactive les colonnes/lignes de marker : `on` : activé, `off`, désactivé. Certaines mises en pages surchargent cette valeur. |
| `@show_dots`     | `off`      | Affiche ou masque les points de positionnement des syllabes : `on` = affichés, `off` = masqués (défaut). Les syllabes conservent leur position dans les deux cas (le point occupe toujours sa sous-partie de case). |
| `@end_circle`    | —          | **Déprécié** |
| `@font_style`    | `mincho`   | Police de rendu : `mincho` (Hiragino Mincho ProN, YuMincho, MS PMincho, Noto Serif CJK JP) ou `gothic` (Hiragino Kaku Gothic ProN, Yu Gothic, Meiryo, MS Gothic, Noto Sans CJK JP). La police réelle dépend du système qui affiche le SVG.    |
| `@shaku_circled` | `off`      | Rend les 尺 entourés d'un cercle : `on` : activé, `off` : désactivé |
| `@shaku_sharp`   | `off`      | Rend les 尺♯ accompagnés du symbole ♯ : `on` : activé, `off` : désactivé |
| `@lyrics_size`   | `medium`   | Taille de police des couplets : `small` = 50%, `medium` = 75%, `big` = 100% de la taille de base |
| `@lyr_blocks`    | `1`        | Nombre de **blocs de paroles** par page (unique à l'échelle d'une chanson ; peut varier d'une chanson à l'autre d'une compilation). Défaut du layout (`lyr_blocks`), plafonné à `lyr_blocks_max` : chindami accepte 2, voire 3 (sinon 1). Blocs chaînés haut→bas (spanning vertical, comme mega), hauteurs égales couvrant tout le kihon hanmen, gap `lyr_block_gap` entre blocs (chindami : 0,7 cm). Valeur invalide/hors bornes → WARNING + défaut |
| `@kinsoku`       | `simple`   | Kinsoku (禁則処理, [JLREQ W3C](https://www.w3.org/TR/jlreq/)) au repli des paroles `::lyrics` quand une ligne est coupée au caractère (layout `chindami`) : `simple` = 行頭禁則 avec追い出し (fermetures, ponctuation 、。，・：；, 々〻, ー, petits kana) + 行末禁則 (ouvrantes), `strict` = ajoute ！？ en tête de ligne, `off` = coupe au caractère (comportement historique). En vertical, tête de ligne 行頭 = haut de la pile, fin de ligne 行末 = bas : le追い出し fait descendre le caractère interdit en fin de ligne courante, qui s'allonge d'une unité (ce n'est PAS un ぶら下げ組, non implémenté). Défaut `simple`, sauf `nomura` (`off` : pas de repli des paroles au caractère). `--kinsoku` en CLI. |
| `@text_color`    | `#000000`    | Couleur de **tout le texte**, format HTML (`#rgb`, `#rrggbb` ou nom CSS, ex. `red`). Surcharge le défaut du design de la mise en page |
| `@frame_color`   | défaut du layout | Couleur du filet de cadre de page (layout `nomura` seul à ce jour), format HTML. Défaut `nomura` : `#333333` |
| `@frame_width`   | défaut du layout | Épaisseur du filet de cadre, en pt (nombre positif ou nul). **`0` = cadre non affiché** (le cadre virtuel se confond alors avec le hanmen). Défaut `nomura` : `1.5`, autres layouts : `0` |
| `@cell_color`    | défaut du layout | Couleur des cases et de la bande marker, format HTML. Défauts : `#bbbbbb` (vertical, chindami, mega), `#999999` (horizontal, tuto), `#333333` (nomura) |
| `@cell_width`    | défaut du layout | Épaisseur des filets de cases, en pt. Défauts : `0.75` (vertical, horizontal, tuto, mega), `0.6` (nomura, chindami) |
| `@arrow_color`   | défaut du layout | Couleur des flèches de répétition `|: :|` et des symboles vocaux ⚪⚫, format HTML. Mêmes défauts que `@cell_color` |
| `@arrow_width`   | défaut du layout | Épaisseur des flèches de boucles, en pt. Mêmes défauts que `@cell_width` |
| `@rep_fill`     | `off`      | Têtes des **flèches de répétition instrumentale** `|: :|` : `on` = remplies (couleur `@arrow_color`), `off` = creuses (défaut). Ancien nom `@arrow_fill` accepté et rectifié en `@rep_fill` par le cleaner |
| `@vrep_fill`    | `off`      | **Disques de répétition vocale** `(: :)` : `on` = remplis (couleur `@arrow_color`), `off` = creux (défaut) — indépendant de `@rep_fill` |
| `@circle_width` | défaut du layout | Épaisseur du **cercle de 尺** (`@shaku_circled on`), nombre positif (pt). Défauts : `1` partout, `0.5` en chindami |
| `@ruby_size`     | `50`       | Taille de police du ruby, en % de la taille de base. **Non utilisé à ce jour** |

Ces 10 attributs de design sont définis dans chaque mise en page (champs `text_color`, `frame_color`, `frame_width`, `cell_color`, `cell_width`, `arrow_color`, `arrow_width`, `rep_fill`, `vrep_fill`, `circle_width` du `LayoutSpec` de `kkml2svg.py`) ; la métadonnée KKML correspondante surcharge le défaut du layout. Une valeur invalide (couleur non HTML, épaisseur non positive, `rep_fill`/`vrep_fill` autre que `on`/`off`) est ignorée avec un `AVERTISSEMENT` et le défaut du layout s'applique. Chindami : `cell_width = arrow_width = 0.4` (filets 0,4 pt), `rep_fill = on` par défaut (flèches instrumentales pleines : seule la tête est remplie, la queue en L du path porte `fill="none"`), `vrep_fill = off` (disques vocaux creux), `circle_width = 0.5` (cercles de 尺).
| `@musicno`       | —          | Numéro de morceau (champ Portama `musicno`, entier). Valeur stockée telle quelle ; affichée en layout `chindami` (tronquée mod 1000 si > 999) |
| `@chogen`        | `5`        | Accordage absolu en demi-tons (champ Portama `chogen`, chaîne, ex. `"5"`). Valeur stockée telle quelle. Se déduit de `@base_note` et vice-et-versa. |
| `@speed`         | —          | Tempo en bpm (champ Portama `speed`, chaîne, ex. `"68"`). Rendu `♩=120` en horizontal, fs 12, sans espace : à droite du titre avant `@choshi` (layouts horizontaux sauf tuto), sous le titre centré au-dessus de `@choshi` (vertical, chindami, nomura, mega), page de titre sous le titre (tuto) |
| `@rythm`         | —          | Rythme (champ Portama `rhythm`, chaîne). Valeur stockée telle quelle          |
| `@rythm_mode`    | —          | Mode rythmique (champ Portama `rhythmMode`, chaîne). Valeur stockée telle quelle |

Toutes les métadonnées sont optionnelles. L'ordre est sans importance. Les métadonnées peuvent être localisées à tout début de ligne, y compris après des sections. Toute métadonnée s'applique à l'ensemble du fichier.
En cas de doublon, la première occurrence prime.
Les mises en page ou la ligne de commande peuvent surcharger certaines métadonnées, qui sont alors ignorées.

## Sections

### Chanson nommée
`::part nom` — nom de chanson (partie d'une compilation), s'applique au bloc suivant (utile en layout `mega` pour un medley : le nom de chaque chanson est imprimé au-dessus de ses colonnes). `::parts nom` (pluriel), `::song nom` et `::section nom` sont d'anciens noms acceptés comme alias de `::part nom` (renommés avec une info stderr) — `::song` renommé en `::part` le 2026-11-23 ; `::section` était trop générique, `::tab` étant déjà une section.

De même, les fautes de frappe usuelles sont acceptées comme alias et rectifiées
en nom canonique par `kkml_clean.py` (avec une info stderr au parsing) :
`::tabs` → `::tab`, `::vocals` → `::vocal`, `::lyric` → `::lyrics`, `::parts`/`::songs`/`::song`/`::section` → `::part`.

### Sauts de mise en page (layout `mega` uniquement)
`::block` — ferme le bloc horizontal courant et passe au bloc suivant ; le bloc sauté est rempli de *dans* vides jusqu'à son nombre de colonnes prévues (`dans_per_block` du bloc). `::page` — idem, puis la page courante est complétée de blocs vides et on passe à la page suivante. Sans contenu ; ignorés par les autres layouts.

### Tab
`::tab` — section de tablature, organisée en temps (figures), séparés par des espaces.
**Boucle vocale** : `(:` en début de token, `:)` en fin (ex. `(:合`, `中:)`), rendue comme marqueur de boucle dans la colonne marker. **Désambiguation** : les marqueurs de boucle (`|:`, `:|`, `(:`, `:)`) ne figurent QUE dans `::tab` ; les koedashi/koekiri (`(`, `)`) ne figurent QUE dans `::vocal`. Un `( )` dans `::tab` est ignoré avec un avertissement ; une boucle dans `::vocal` est ignorée avec un avertissement. Les sauts de lignes sont interprétés comme des espaces, ainsi les lignes ne correspondent pas obligatoirement aux dans de la mise en page.

`::` ferme la section courante.

### Vocal
`::vocal` — chant syllabique aligné sur les temps de la tablature : un mot (séparé par des espaces) = une syllabe, les points `.` subdivisent le temps en parts égales. En mise en page verticale (`vertical`, `chindami`, `mega`), une syllabe en deux parties (grand kana + petit kana, ex. `ちゅ`) est rendue avec le petit kana tassé à droite du grand, à la même taille de police (le glyphe petit kana est nativement plus petit dans le cadratin : グヮ vs グワ — conforme JLREQ cl-11) ; `nomura`, `horizontal` et `tuto` ne changent pas. Chaque ligne de `::vocal` correspond à la ligne de `::tab` de même index (la syllabe i reste alignée sur la note i ; une ligne de chant plus courte est complétée par des cases vides). Un token `ー`/`ｰ`/`－` ISOLÉ vaut case vide ; collé à une syllabe (ex. `よー`) il reste la voyelle longue. Un choonpu isolé **littéral** (voyelle longue seule dans une case, ex. 唐船ドーイ) s'écrit échappé : `\ー` (antislash + `ー` ; variantes `ｰ` `－` acceptées, normalisées en `\ー`) — jamais pris pour une case vide, rendu `ー` (tourné à 90° en vertical, à plat en horizontal). Les `(` / `)` (koedashi/koekiri) sont rendues `○` / `□` dans la case, alignées sur la sous-partie (syllabe ou point `.`, même non affiché) à laquelle la borne est rattachée : `(` → élément juste après, `)` → élément juste avant (toutes les mises en page sauf `tuto`) ; en layout `horizontal`, alignées en y sur la centerline du tiers inférieur de la case. **Désambiguation** : `(` / `)` (koedashi/koekiri) ne figurent QUE dans `::vocal` ; les boucles `|: :| (: :) |( )|` y sont ignorées avec avertissement (réservées à `::tab`). Les anciennes sections `::tab-lyrics` et `::tab-vocals` sont des alias dépréciés de `::vocal` (acceptés avec une info stderr).

`::` ferme la section courante.

### Lyrics
`::lyrics` — section de paroles, divisé en couplets. Séparateurs de couplets : ligne vide, OU marqueur de couplet en début de ligne (voir ci-dessous) — un marqueur force le changement de couplet même sans ligne vide, et donc un saut de ligne en layout vertical (nouvelle ligne 行, avance de ligne 行送り horizontale droite→gauche). Chaque caractère `|`, où qu'il soit dans la ligne source, ferme la ligne (行) courante et en ouvre une suivante ; `||` ferme la ligne et insère en plus une ligne blanche avant le contenu suivant. Une ligne source sans aucun `|` s'enchaîne dans la ligne courante (les segments se suivent sur la même ligne, 1 espace). Les espaces autour du `|` (simple ou pleine chasse, ex. `phrase|　奥ぬ…` ou `phrase | suite`) sont du formatage visuel du KKML brut et sont ignorés au rendu — `|` suivi d'espaces s'interprète comme `|` seul. Marqueurs de début de couplet reconnus :
  - `⚪︎` `⚫︎` `○` `●` `・` ou `、` — marqueur générique.
  - `一、` `二、` `三、` etc. — numéro de couplet (numéraux CJK + virgule japonaise pleine largeur `、`). 
  - `①` `②` `③` … jusqu'à `⑳` (U+2460–U+2473) — numéro de couplet (virgule `、` facultative après, ex. `①、`). 
  - `女` `男` `男女` suivis de `、` (virgule pleine chasse, ex. `女、`) ou d'un espace (ex. `女　`) — couplet chanté par les femmes `女`, les hommes `男` ou les deux `男女`. 
    Plusieurs types de couplets peuvent être mélangés dans un même morceau.

Variantes phonétiques des paroles : `::lyrics-kanji`, `::lyrics-ruby`, `::lyrics-romaji`, `::lyrics-kana` —
  pour les chansons dont on conserve plusieurs versions phonétiques (par ex. une en kanji pour les japonais,
  une en romaji pour les étrangers). Toutes ces variantes partagent la grammaire et le rendu de `::lyrics`
  (couplets, lignes `|`/`||`, rubys). `::lyrics` est un alias de `::lyrics-ruby` : kanji avec support des rubys.
  `::lyrics-kanji` désigne une version en kanjis seuls (sans rubys), `::lyrics-kana` une transcription en kanas,
  `::lyrics-romaji` une romanisation.

`::` ferme la section courante.

## Ruby

Le ruby (furigana) est un guide phonétique placé à droite du texte de base en écriture verticale, ou au-dessus en écriture horizontale. Il permet de préciser la lecture des caractères kanji ou kana, ce qui est particulièrement utile dans les langues Ryukyu, car leurs lectures dévient fréquemment du japonais standard, y compris les lectures de kanas dans certains cas (ex. の pouvant être lu ぬ). Même en japonais standard, le ruby reste utile pour les musiciens peu à l'aise avec la lecture des kanjis et/ou dans le cas des kanjis rares.

Trois syntaxes sont possibles pour encoder les rubys en KKML :

| Syntaxe          | Type       | Description | Exemple |
|------------------|------------|-------------|---------|
| ` X《a》`        | Mono-ruby   | Le dernier caractère avant `《》` est la base | ` 安《あ》` → 安+あ |
| `｛XYZ｝《abc》`  | Group-ruby  | Le texte entre `｛｝` est la base groupée | `｛安里屋｝《あさとや》` → 安里屋+あさとや |
| `｛X《a》Y《b》｝` | Jukugo-ruby | Groupe avec annotations individuelles | `｛安《あ》里《さと》屋《や》｝` → 安+あ, 里+さと, 屋+や |

Détails :
- `《》` (U+300A / U+300B) = chevrons japonais pleine largeur, délimitent l'annotation
- `｛｝` (U+FF5B / U+FF5D) = accolades pleine largeur, délimitent le groupe de base
- En mono-ruby sans `｛｝`, seul le caractère placé immédiatement avant `《》` est annoté. Le texte précédent est rendu sans ruby.
- Échappement : `\《` `\》` `\｛` `\｝` (antislash + délimiteur) produisent le caractère littéral, non interprété comme ruby/groupe (ex. `x\《y》` affiche `x《y》` sans ruby). L'antislash n'est retiré que devant ces 4 caractères ; ailleurs il reste littéral. Valable dans les métadonnées et les paroles.

### Liens hypertexte (métadonnées uniquement)
- Syntaxe Markdown dans les valeurs de métadonnées affichées (`@title`, `@author`, `@composer`, `@lyricist`, `@origin`, `@genre`) : `[label](url)` — seul le `label` est affiché, rendu cliquable (`<a xlink:href="url">`) dans le SVG. Ex. `@source [Portama](https://exemple.jp/)`.
- Le `label` peut contenir du ruby (`《》` `｛｝`) ; l'`url` ne doit pas contenir de parenthèses et n'est jamais affichée.
- `\[` et `\]` produisent un crochet littéral (pour écrire `[x](y)` en clair).
- Les liens ne sont pas interprétés dans les paroles (`::lyrics`) ni dans `::tab`/`::vocal`.
- En KKML, le ruby peut être utilisé dans les métadonnées affichées `@title` `@author`, `@composer`, `@lyricist`, `@origin`, `@genre` ainsi que dans les sections `::lyrics` (et ses variantes `::lyrics-kanji` `::lyrics-ruby` `::lyrics-kana` et `::lyrics-romaji`). Il n'est pas utilisable pour les autres métadonnées et sections. En particulier, `::tab` est basé sur une syntaxe qui ne doit pas être altérée par un ruby,  et `::vocal` est par construction déjà écrit en phonétique.

- ✅ (2026-11-20) Décision : les délimiteurs restent `《》` / `｛｝` (pas de passage aux yamakakko `〈〉`) ; le besoin de caractères littéraux est couvert par l'échappement par antislash ci-dessus.

## Cellules de tablature

Chaque cellule de tablature correspond à un temps. Les tablatures Kunkunshi ignorent la notion de mesure (regroupement de temps tels que 3/4 ou 4/4).

Séparateurs à l'intérieur d'une figure (dans une cellule) :

| Séparateurs  | Figure rythmique                        | Exemple              |
|--------------|-----------------------------------------|----------------------|
| (sans objet) | Une noire                               | `合`                  |
| `/`          | Deux croches                            | `合/工`               |
| `//`         | Quatre doubles croches                  | `合//工//中//上`       |
| `/` `//`     | Une croche et deux double croches       | `合/工//中`           |
| `//` `/`     | Deux double croches et une croche       | `合//工/中`           |
| `/` avec `-` à gauche | Note à cheval seule (pas de note principale — Portama : cellule principale vide + straddle) | `-/合` |
| `/` en tête de bloc | **Straddle de tête** (rang -1) : note à cheval sur le bord *précédent* de la 1re case (haut en vertical, gauche en horizontal) — token `/B` en tout premier token du bloc `::tab` ; ne consomme pas de case ; hors tête de bloc : avertissement + ignoré. Rendu : vertical, horizontal, mega | `/六` |
| `:`          | Une croche pointée et une double croche | `合:工`               |
| `::`         | Une double croche et une croche pointée | `合::工`              |
| `+` `=` `-`  | Accord (notes simultanées, max 3) — `+` canonique, `=` et `-` variantes acceptées | `四+工`, `四=工` ou `合+四+工` |
| (aucun)      | Position étendue, altération, etc.      | `下老`, `イ尺`, `尺♯`… |

Suffixes accolés à la note (techniques de jeu `souhou`, doigtés `yubii`) : voir [notation.md](notation.md). En particulier, les doigtés se notent ㊀㊁㊂㊃ (U+3280-U+3283) en suffixe de la note (ex. `合㊀`) — jamais seuls dans une case (confusion avec le silence ◯).

TODO: risque de collision entre :: et la fin de section.

En cas de figure non reconnue (ni position, ni séparateur, ex. `合工尺`), le convertisseur émet une alerte sur stderr (une seule fois par figure unique) et applique un rendu dégradé — les 3 premiers caractères au maximum, condensés en largeur comme `イ中` (2 caractères) ou `イ下尺` (3 caractères). L'ancien comportement « ornement » (empilement vertical de tous les caractères) est déprécié : il n'a pas de sémantique musicale (les kanji empilés réels sont des croches `A/B`, du hayabiki `A:B` ou des accords `A+B`, chacun ayant son séparateur).

**DÉPRÉCIÉ (2026-11-01)** — anciennement marqueurs autonomes `|(` (vocalRepStart) et `)|` (vocalRepEnd), encore acceptés avec un AVERTISSEMENT. La boucle vocale se note désormais dans `::vocal` avec `(:` ... `:)`. — répétition du chant (section reprise au chant/à la piste suivante, mécanique Portama). Contrairement aux suffixes `(` `)` 声だし/声切り, ils ne sont pas attachés à une note et peuvent occuper une case vide.

Rendu : les marqueurs `|(` et `)|` vivent dans la colonne marker (comme les flèches de `|:` / `:|`) — les kanjis de notes ne sont JAMAIS décalés, le contenu de la case est rendu centré normalement. `)|` = ┘● : barre horizontale, montant vertical montant, disque creux au-dessus (même géométrie et même taille que l'ancien `@end_circle`, désormais déprécié et ignoré) ; `|(` = image spéculaire par rapport à l'axe HORIZONTAL : barre en haut, montant vertical descendant, disque creux en dessous.

Composition : le marqueur partage librement sa case avec du contenu, rendu centré sans décalage. Exemples : `|((◯` = début de boucle vocale + 声だし + repos (cas 安波節 : le chant commence pendant un silence du sanshin) ; `|(尺)` = ┘○ miroir + 尺 + 声切り ; `◯)|` = fin de boucle posée sur un repos ; `合)|` = fin de boucle sur une note.
| `ー` `ｰ` `－` (symbole isolé) | `-` | case vide (dans `::tab` comme dans `::vocal`). Un ー collé à un kanji (ex. `中ー`) reste une figure non reconnue dans `::tab` ; dans `::vocal`/`::lyrics` collé à une syllabe il reste la voyelle longue, on ne devine pas l'intention |

L'espace séparateur entre une clé de métadonnée et sa valeur est lui aussi toléré absent : `@title｛安波節｝《あはぶし》` (sans espace après `@title`) est reconnu comme `@title ｛安波節｝…`, avec une info stderr par clé concernée.

Les espaces multiples et l'espace pleine chasse `　` (U+3000) sont de toute façon des séparateurs de figures valides. Dans les sections `::lyrics`, `｜` (U+FF5C) est normalisé en `|` — les sauts de ligne (`|` / `‖`) et séparateurs de couplets s'écrivent indifféremment en simple ou double largeur. Dans `::vocal`, un token `ー`/`ｰ`/`－` ISOLÉ est normalisé en `-` (case vide) ; collé à une syllabe, le ー reste une voyelle longue. Dans `::lyrics`, aucune normalisation (le ー y reste une voyelle longue).

Rendu vertical des paroles : une ligne de couplet (行) qui commence par un marqueur de couplet (一、二、… ①②③… 女　男　) est alignée en haut de la zone de paroles (行頭) ; les lignes de continuation (après `|`) s'indentent sous le marqueur, le long de la ligne ; une ligne blanche (après `||`) réinitialise l'indentation. La hauteur du canevas couvre la ligne de paroles la plus longue (longueur de ligne 行の長さ), même si elle dépasse la grille.

## Tolérances

### Sections

Si aucune section n'est déclarée, les lignes hors métadonnées et commentaires sont considérées comme une section `::tab` implicite.

### Lignes vides

Au sein des sections `::tab` et `::vocal`, ainsi que hors des sections, les lignes vides sont ignorées.

### Réduction de caractères vers leur forme canonique

#### Caractères en double largeur vers caractères en simple largeur

Au sein des sections `::tab` et `::vocal`, les équivalents pleine largeur des signes en demie-largeur ci-dessous sont tolérés. C'est toutefois la forme en demie-largeur qui est canonique. 

| Double largeur  | Demie-largeur | Usage (pour mémoire)  |
|-----------------|---------------|-----------------------|
| `　` (U+3000)   | ` `           | séparateur de temps   |
| `／` (U+FF0F)   | `/`           | deux croches          |
| `：` (U+FF1A)   | `:`           | croche pointée + double croche, marques de répétition |
| `｜` (U+FF5C)   | `\|`          | marques de répétition |
| `＋` (U+FF0B)   | `+`           | accord (taachi / tsuiri-bichi), forme canonique |
| `＝` (U+FF1D)   | `=`           | accord (taachi / tsuiri-bichi), variante de +   |
| `ー` (U+30FC)   | `-`           | case vide uniquement - ne pas normaliser sinon  |
| `｀` (U+FF40)   | `'`           | uchi-utu (打音) |
| `＊` (U+FF0A)   | `*`           | uchi-utu (打音), variante de `｀` et `'` |
| `＂` (U+FF02)   | `"`           | uchi-nuchi-utu (打ち抜き音) |
| `〃` (U+3003)   | `"`           | uchi-nuchi-utu (打ち抜き音) |
| `＾` (U+FF3E)   | `^`           | kaki-utu (掛音) |
| `＜` (U+FF1C)   | `<`           | kachi-utu (掻音) |
| `（` (U+FF08)   | `(`           | koedashi, début de boucle vocale |
| `）` (U+FF09)   | `)`           | koekiri, fin de boucle vocale  |

#### Altérations

Au sein des sections `::tab` et `::vocal`, les équivalents UTF-8 des signes ASCII ci-dessous sont tolérés. C'est toutefois la forme ASCII qui est canonique. 

| UTF-8           | ASCII | Usage (pour mémoire) |
|-----------------|-------|----------------------|
| `♯` (U+266F)    | `#`   | Dièse                |
| `♭` (U+266D)    | `b`   | Bémol                |

En **suffixe d'une note quelconque** (ex. `合♯`, `合♭`), `♯`/`♭` denote une altération (champ `acc` de Portama : `sharp`/`flat`), rendue en haut-droite de la note à ≈ 48 % de sa taille. Cas spécial : `尺♯` (U+5C3A U+266F) reste indivisible au format, mais est décomposé au rendu (note + marque ♯ standard) ; `@shaku_sharp off` masque le ♯, et un shaku altéré n'est jamais cerclé (`@shaku_circled`).

#### Caractères graphiquement similaires

Au sein des sections `tab::`, certains symboles/caractères graphiquement similaires à leur forme canonique sont tolérés.

| Symbole       | Forme canonique | Usage (pour mémoire) |
|---------------|-----------------|----------------------|
| `○` (U+25CB)  | `◯` (U+25EF)   | Repos                |
| `〇` (U+3007) | `◯` (U+25EF)   | Repos                |
| `⚪` (U+26AA) | `◯` (U+25EF)   | Repos (les sélecteurs de variante U+FE00-FE0F sont retirés des tokens, ex. `⚪︎` = U+26AA U+FE0E) |

Préfixe `口` (U+53E3, radical) accepté comme variante de `ロ` (U+30ED) dans les positions hautes à 2 caractères (ex. `口上` = `ロ上`).

#### Kandokoro en romaji vers kandokoro en kanji

Au sein des sections `tab::`, les kandokoro exprimés en romaji sont tolérés ; c'est toutefois la forme en kanji qui est canonique. Cette tolérance vise à permettre la saisie de tablatures par un utilisateur qui ne disposerait pas d'un système de saisie en japonais.

| Romaji   | Kanji<br>(Canonique) |
|----------|---------|
| `ai`     | `合`    |
| `otsu`   | `乙`    |
| `ro`     | `老`    |
| `rou`    | `老`    |
| `rō`     | `老`    |
| `shi`    | `四`    |
| `yon`    | `四`    |
| `jo`     | `上`    |
| `jou`    | `上`    |
| `jō`     | `上`    |
| `jyo`    | `上`    |
| `jyou`   | `上`    |
| `jyō`    | `上`    |
| `naka`   | `中`    |
| `chu`    | `中`    |
| `chuu`   | `中`    |
| `chū`    | `中`    |
| `shaku`  | `尺`    |
| `ko`     | `工`    |
| `kou`    | `工`    |
| `kō`     | `工`    |
| `go`     | `五`    |
| `roku`   | `六`    |
| `shichi` | `七`    |
| `nana`   | `七`    |
| `hachi`  | `八`    |
| `kyu`    | `九`    |
| `kyuu`   | `九`    |
| `kyū`    | `九`    |
| `ju`     | `十`    |
| `juu`    | `十`    |
| `jū`     | `十`    |
| `jyu`    | `十`    |
| `jyuu`   | `十`    |
| `jyū`    | `十`    |
| `sai`    | `才`    |
| `bon`    | `凡`    |
| `dshaku` | `勺`    |

NB: dshaku pour "down shaku". sai, bon et dshaku ne peuvent pas être utilisés dans les sections existantes ; ils auront leur place dans une future section dédiée à la hauteur de chant, nécessaire pour pouvoir rendre complètement les recueils nomura-ryu.

TODO: séparer explicitement les méthodes Hepburn et Kunrei (et Nippon-shiki ?)

#### Kandokoro en chiffres romains vers kandokoro en kanji

Au sein des sections `tab::`, les kandokoro exprimés en chiffres romaji sont tolérés ; c'est toutefois la forme en kanji qui est canonique. 

| Chiffre  | Kanji<br>(Canonique) |
|----------|---------|
| `4`      | `四`    |
| `5`      | `五`    |
| `6`      | `六`    |
| `7`      | `七`    |
| `8`      | `八`    |
| `9`      | `九`    |
| `10`     | `十`    |

#### Positions étendues en kanji composite vers positions étendues en katakana + kanji

Au sein des sections `tab::`, les kandokoro étendus exprimés sous la forme d'un kanji composite sont tolérés ; c'est toutefois la forme katakana + kanji qui est canonique.

| Kanji          | Katakana + Kanji<br>(Canonique) |
|----------------|------------------|
| `佮` (U+4F2E)  | `イ合`            |
| `亿` (U+4EBF)  | `イ乙`            |
| `佬` (U+4F6C)  | `イ老`            |
| `伵` (U+4F75)  | `イ四`            |
| `仩` (U+4EE9)  | `イ上`            |
| `仲` (U+4EF2)  | `イ中`            |
| `伬` (U+4F2C)  | `イ尺`            |
| `仜` (U+4EDC)  | `イ工`            |
| `伍` (U+4F0D)  | `イ五`            |
| `仈` (0x4EC8)  | `イ八`            |
| `仇` (U+4EC7)  | `イ九`            |
| `㕶` (U+3576)  | `ロ五`            |
| `呎` (U+544E)  | `ロ尺`            |
| `叿` (U+53FF)  | `ロ工`            |
| `呬` (U+546C)  | `ロ四`            |
| `哈` (U+54C8)  | `ロ合`            |
| `咾` (U+54BE)  | `ロ老`            |
| `𠮟` (U+20B9F) | `ロ七`            |
| `叱` (U+53F1)  | `ロ七`            |
| `叭` (U+53ED)  | `ロ八`            |
| `㕤` (U+3564)  | `ロ九`            |

## Bonnes pratiques

Ces bonnes pratiques visent à faciliter l'exécution du morceau en ayant le fichier KKML brut sous les yeux.
- Il est **recommandé** de faire figurer la section tab:: en haut, juste sous les métadonnées, et plus généralement, de placer les sections dans l'ordre suivant `::tab` `::vocal` `::lyrics`
- Il est **recommandé** d'adopter le même découpage en lignes dans `tabs::` et `tabs-lyrics::`

## Pour en savoir plus

Voir [notation musicale](notation.md) pour le détail des figures, modes rythmiques, suffixes de technique, positions étendues et options d'en-tête.
