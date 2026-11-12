# Référence du format KKML

Le KKML (Kunkunshi Markup Language) est un format texte destiné à l'encodage des tablatures Kunkunshi. L'objectif est de proposer une alternative au format JSON de Portama, qui réponde aux défis suivants :
- Facile à saisir à l'aide d'un éditeur de texte,
- Non dépendant de polices spécifiques (une police japonaise compatible UTF-8 suffit),
- Un musicien doit pouvoir exécuter le morceau en ayant le fichier KKML brut (non rendu) sous les yeux.

Par ailleurs, KKML tente de combler des certains manques inhérents au format JSON de Portama : suppor de positions étendues manquantes, de figures rythmiques non prises en charge, etc.

En développant KKML et ses outils, nous espérons rendre la création de tablatures Kunkunshi accessible à tous !

## Format source

KKML se base sur le format texte brut encodé en UTF-8, sans utilisation des extensions PUA (private use area).

## Structure générale

```
# commentaire (ignoré)
@meta valeur
@cells_per_dan 12

::section
contenu
::

::tab
<tablature sous forme de cases représentant des temps, séparées par des espaces ;
au sein de chaque case, figures représentant des notes, leurs altérations et leurs
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

| Clé              | Défaut     | Description |
|------------------|------------|-------------|
| `@format`        | `KKML`     | Format de fichier |
| `@version`       | —          | Numéro de version du format |
| `@title`         | —          | Titre du morceau (ruby supporté) |
| `@genre`         | —          | Genre musical. **Déprécié** |
| `@author`        | —          | Auteur du morceau (ruby supporté) |
| `@composer`      | —          | Compositeur (ruby supporté) |
| `@lyricist`      | —          | Parolier (ruby supporté) |
| `@origin`        | —          | Origine (ruby supporté) |
| `@comment`       | —          | Commentaire |
| `@tuning`        | `本調子`   | Accordage relatif. Valeurs connues : `本調子`, `二揚げ`, `三下げ`, `一二揚げ`, `一揚げ` |
| `@base_note`     | `C3`       | Note de base : hauteur de la position 合 (accordages 本調子, 二揚げ, 三下げ) ou 合 moins 2 demi-tons (一二揚げ, 一揚げ) |
| `@layout`        | `vertical` | Modèle de rendu : `vertical`, `horizontal`, `nomura`, `chindami` ou `tuto` (voir [svg-layout.md](svg-layout.md)) |
| `@page_dans`     | —          | Pagination multipage : nombre max de dans par page (un SVG par page de N dans). `-p/--page-dans N` en CLI |
| `@tuto_block`    | `1280x720` | Layout `tuto` uniquement : dimensions du bloc en pixels (`LxH`) ; chaque page SVG fait exactement LxH |
| `@cells_per_dan` | —          | Nombre de cellules par dan = propriété de mise en page, pas de la chanson. Ignoré au rendu ; utilisé par `kkml_cleaner.py` comme indice de repli (jamais de valeur par défaut : ne pas écraser les sauts de ligne choisis par l'utilisateur) ; `-c` en CLI pour vertical/horizontal (chindami et nomura imposent 12 cellules/dan). Ancien nom `@cols` accepté (renommé par le cleaner) |
| `@marker`        | `on`       | Active/désactive le marker (concept sémantique ; rendu en colonne/ligne marker selon le layout) : `on`/`off` |
| `@end_circle`    | —          | **Déprécié**, ignoré |
| `@font_style`    | `mincho`   | Police de rendu : `mincho` (Hiragino Mincho ProN, YuMincho, MS PMincho, Noto Serif CJK JP) ou `gothic` (Hiragino Kaku Gothic ProN, Yu Gothic, Meiryo, MS Gothic, Noto Sans CJK JP). La police réelle dépend du système qui affiche le SVG |
| `@shaku_circled` | `off`      | Rend les 尺 entourés d'un cercle : `on`/`off` |
| `@shaku_sharp`   | `off`      | Rend les 尺♯ accompagnés du symbole ♯ : `on`/`off` |
| `@lyrics_size`   | `medium`   | Taille des couplets : `small` = 50%, `medium` = 75%, `big` = 100% de la taille de base |
| `@ruby_size`     | `50`       | Taille du ruby en % de la taille de base. Non utilisé à ce jour |
| `@musicno`       | —          | Numéro de morceau (pour compatibilité Portama) |
| `@chogen`        | —          | Accordage absolu (pour compatibilité Portama)  |
| `@speed`         | —          | Tempo (pour compatibilité Portama)             |
| `@rythm`         | —          | Rythme (pour compatibilité Portama)            |
| `@rythm_mode`    | —          | Mode rythmique (pour compatibilité Portama)    |

Toutes les métadonnées sont optionnelles. L'ordre est sans importance. Les métadonnées peuvent être localisées à tout début de ligne, y compris après des sections. Toute métadonnée s'applique à l'ensemble du fichier.
En cas de doublon, la première occurrence prime.

## Section

- `::tab` — section de tablature, organisé en temps (figures), séparés par des espaces. **Boucle vocale** : `(:` en début de token, `:)` en fin (ex. `(:合`, `中:)`), rendue comme marqueur de boucle dans la colonne marker. **Désambiguation** : les marqueurs de boucle (`|:`, `:|`, `(:`, `:)`) ne figurent QUE dans `::tab` ; les koedashi/koekiri (`(`, `)`) ne figurent QUE dans `::vocal`. Un `( )` dans `::tab` est ignoré avec un avertissement ; une boucle dans `::vocal` est ignorée avec un avertissement. Les sauts de lignes sont interprétés comme des espaces, ainsi les lignes ne correspondent pas obligatoirement aux dans de la mise en page.
- `::vocal` — chant syllabique aligné sur les temps de la tablature : un mot (séparé par des espaces) = une syllabe, les points `.` subdivisent le temps en parts égales. Chaque ligne de `::vocal` correspond à la ligne de `::tab` de même index (la syllabe i reste alignée sur la note i ; une ligne de chant plus courte est complétée par des cases vides). Un token `ー`/`ｰ`/`－` ISOLÉ vaut case vide ; collé à une syllabe (ex. `よー`) il reste la voyelle longue. **Désambiguation** : `(` / `)` (koedashi/koekiri) ne figurent QUE dans `::vocal` ; les boucles `|: :| (: :) |( )|` y sont ignorées avec avertissement (réservées à `::tab`). Les anciennes sections `::tab-lyrics` et `::tab-vocals` sont des alias dépréciés de `::vocal` (acceptés avec une info stderr).
- `::lyrics` — section de paroles, divisé en couplets. Séparateurs de couplets : ligne vide, OU marqueur de couplet en début de ligne (voir ci-dessous) — un marqueur force le changement de couplet même sans ligne vide, et donc un saut de colonne en layout vertical. Chaque caractère `|`, où qu'il soit dans la ligne, ferme la colonne courante et ouvre la suivante ; `||` ferme la colonne et insère en plus une colonne blanche avant le contenu suivant. Une ligne sans aucun `|` s'enchaîne dans la colonne courante (saut de ligne = 1 espace). Les espaces autour du `|` (simple ou pleine chasse, ex. `phrase|　奥ぬ…` ou `phrase | suite`) sont du formatage visuel du KKML brut et sont ignorés au rendu — `|` suivi d'espaces s'interprète comme `|` seul. Marqueurs de début de couplet reconnus :
  - `⚪︎` `⚫︎` `・` ou `、` — marqueur générique.
  - `一、` `二、` `三、` etc. — numéro de couplet (numéraux CJK + virgule japonaise pleine largeur `、`). 
  - `女` `男` `男女` suivis de `、` (virgule pleine chasse, ex. `女、`) ou d'un espace (ex. `女　`) — couplet chanté par les femmes `女`, les hommes `男` ou les deux `男女`. 
    Plusieurs types de couplets peuvent être mélangés dans un même morceau.
- Variantes phonétiques des paroles : `::lyrics-kanji`, `::lyrics-ruby`, `::lyrics-romaji`, `::lyrics-kana` —
  pour les chansons dont on conserve plusieurs versions phonétiques (par ex. une en kanji pour les japonais,
  une en romaji pour les étrangers). Toutes ces variantes partagent la grammaire et le rendu de `::lyrics`
  (couplets, colonnes `|`/`||`, rubys). `::lyrics` est un alias de `::lyrics-ruby` : kanji avec support des rubys.
  `::lyrics-kanji` désigne une version en kanjis seuls (sans rubys), `::lyrics-kana` une transcription en kanas,
  `::lyrics-romaji` une romanisation.
- `::` ferme la section courante.

## Ruby

Le ruby est un guide phonétique placé à droite du texte de base en écriture verticale, ou au-dessus en écriture horizontale. Il permet de préciser la lecture des caractères kanji ou kana, ce qui est particulièrement utile dans les langues Ryukyu (okinawaïennes) car leurs lectures divergent fréquemment du japonais standard, y compris les lectures de kanas dans certains cas (ex. の pouvant être lu ぬ). Même en japonais standard, le ruby reste utile pour les musiciens peu à l'aise avec la lecture des kanjis et/ou dans le cas des kanjis rares.

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
- En KKML, le ruby peut être utilisé dans les métadonnées `@title` `@author`, `@composer`, `@lyricist`, `@origin`, `@genre` ainsi que dans les sections `::lyrics` (et ses variantes `::lyrics-kanji` `::lyrics-ruby` `::lyrics-kana` et `::lyrics-romaji`). Il n'est pas utilisable pour les autres métadonnées et sections. En particulier, `::tab` est basé sur une syntaxe qui ne doit pas être altérée par un ruby,  et `::vocal` est par construction déjà écrit en phonétique.

## Cases de tablature

Chaque case de tablature correspond à un temps. Les tablatures Kunkunshi ignorent la notion de mesure (regroupement de temps tels que 3/4 ou 4/4).

Séparateurs à l'intérieur d'une figure (dans une case) :

| Séparateurs | Figure rythmique                        | Exemple              |
|-------------|-----------------------------------------|----------------------|
|             | Une noire                               | `合`                  |
| `/`         | Deux croches                            | `合/工`               |
| `//`        | Quatre doubles croches                  | `合//工//中//上`       |
| `/` `//`    | Une croche et deux double croches       | `合/工//中`           |
| `//` `/`    | Deux double croches et une croche       | `合//工/中`           |
| `:`         | Une croche pointée et une double croche | `合:工`               |
| `::`        | Une double croche et une croche pointée | `合::工`              |
| `+` `=` `-` | Accord (notes simultanées, max 3) — `+` canonique, `=` et `-` variantes acceptées (`-` seul = case vide) | `四+工`, `四=工` ou `合+四+工` |
| (aucun)     | Position étendue, altération, etc.      | `下老`, `イ尺`, `尺♯`… |

TODO: risque de collision entre :: et la fin de section.

En cas de figure non reconnue (ni position, ni séparateur, ex. `合工尺`), le convertisseur émet une alerte sur stderr (une seule fois par figure unique) et applique un rendu dégradé — les 3 premiers caractères au maximum, condensés en largeur comme `イ中` (2 caractères) ou `イ下尺` (3 caractères). L'ancien comportement « ornement » (empilement vertical de tous les caractères) est déprécié : il n'a pas de sémantique musicale (les kanji empilés réels sont des croches `A/B`, du hayabiki `A:B` ou des accords `A+B`, chacun ayant son séparateur).

**DÉPRÉCIÉ (2026-11-01)** — anciennement marqueurs autonomes `|(` (vocalRepStart) et `)|` (vocalRepEnd), encore acceptés avec un AVERTISSEMENT. La boucle vocale se note désormais dans `::vocal` avec `(:` ... `:)`. — répétition du chant (section reprise au chant/à la piste suivante, mécanique Portama). Contrairement aux suffixes `(` `)` 声だし/声切り, ils ne sont pas attachés à une note et peuvent occuper une case vide.

Rendu : les marqueurs `|(` et `)|` vivent dans la colonne marker (comme les flèches de `|:` / `:|`) — les kanjis de notes ne sont JAMAIS décalés, le contenu de la case est rendu centré normalement. `)|` = ┘● : barre horizontale, montant vertical montant, disque creux au-dessus (même géométrie et même taille que l'ancien `@end_circle`, désormais déprécié et ignoré) ; `|(` = image spéculaire par rapport à l'axe HORIZONTAL : barre en haut, montant vertical descendant, disque creux en dessous.

Composition : le marqueur partage librement sa case avec du contenu, rendu centré sans décalage. Exemples : `|((◯` = début de boucle vocale + 声だし + repos (cas 安波節 : le chant commence pendant un silence du sanshin) ; `|(尺)` = ┘○ miroir + 尺 + 声切り ; `◯)|` = fin de boucle posée sur un repos ; `合)|` = fin de boucle sur une note.
| `ー` `ｰ` `－` (symbole isolé) | `-` | case vide (dans `::tab` comme dans `::vocal`). Un ー collé à un kanji (ex. `中ー`) reste une figure non reconnue dans `::tab` ; dans `::vocal`/`::lyrics` collé à une syllabe il reste la voyelle longue, on ne devine pas l'intention |

L'espace séparateur entre une clé de métadonnée et sa valeur est lui aussi toléré absent : `@title｛安波節｝《あはぶし》` (sans espace après `@title`) est reconnu comme `@title ｛安波節｝…`, avec une info stderr par clé concernée.

Les espaces multiples et l'espace pleine chasse `　` (U+3000) sont de toute façon des séparateurs de figures valides. Dans les sections `::lyrics`, `｜` (U+FF5C) est normalisé en `|` — les sauts de colonne et séparateurs de couplets s'écrivent indifféremment en simple ou double largeur. Dans `::vocal`, un token `ー`/`ｰ`/`－` ISOLÉ est normalisé en `-` (case vide) ; collé à une syllabe, le ー reste une voyelle longue. Dans `::lyrics`, aucune normalisation (le ー y reste une voyelle longue).

Rendu vertical des paroles : une colonne de couplet qui commence par un marqueur de couplet (一、二、… 女　男　) est alignée en haut de la zone de paroles ; les colonnes de continuation (après `|`) s'indentent sous le marqueur ; une colonne blanche (après `||`) réinitialise l'indentation. La hauteur du canevas couvre la colonne de paroles la plus haute, même si elle dépasse la grille.

## Tolérances

### Sections

Si aucune section n'est déclarée, les lignes hors métadonnées et commentaires sont considérées comme une section `::tab` implicite.

### Lignes vides

Au sein des sections `::tab` et `::vocal`, ainsi que hors des sections, les lignes vides sont ignorées.

### Réduction de caractères vers leur forme canonique

#### Caractères en double largeur vers caractères en simple largeur

Au sein des sections `::tab` et `::vocal`, les équivalents pleine largeur des signes en demie-largeur ci-dessous sont tolérés. C'est toutefois la forme en demie-largeur qui est canonique. 

| Double largeur  | Demie-largeur | Usage (pour mémoire) |
|-----------------|---------------|----------------------|
| `　` (U+3000)   | ` `           | séparateur de temps   |
| `／` (U+FF0F)   | `/`           | deux croches          |
| `：` (U+FF1A)   | `:`           | croche pointée + double croche, marques de répétition |
| `｜` (U+FF5C)   | `\|`          | marques de répétition, séparateur de couplets dans `::lyrics` |
| `♯`  (U+266F)   | `#`           | altération (尺＃) |
| `＋` (U+FF0B)   | `+`           | accord (taachi / tsuiri-bichi), forme canonique |
| `ー` (U+30FC)   | `-`           | case vide uniquement - ne pas normaliser sinon |
| `＊` (U+FF0A)   | `*`           | uchi-utu (打音) |
| `｀` (U+FF40)   | `'`           | uchi-utu (打音) |
| `＂` (U+FF02)   | `"`           | nuchi-utu (打ち抜き音) |
| `＾` (U+FF3E)   | `^`           | kaki-utu (掛音) |
| `＜` (U+FF1C)   | `<`           | kachi-utu (掻音) |
| `＝` (U+FF1D)   | `=`           | accord (taachi / tsuiri-bichi), variante de + |
| `（` (U+FF08)   | `(`           | koedashi, début de boucle vocale |
| `）` (U+FF09)   | `)`           | koekiri, fin de boucle vocale  |

NB: le bémol `♭` (U+266D) n'a pas d'équivalent en demie-largeur ; il ne peut être saisi qu'en pleine largeur.

#### Caractères graphiquement similaires

Au sein des sections `tab::`, certains symboles/caractères graphiquement similaires à leur forme canonique sont tolérés.

| Symbole       | Forme canonique | Usage (pour mémoire) |
|---------------|-----------------|----------------------|
| `○` (U+25CB)  | `◯` (U+25EF)   | Repos                |
| `〇` (U+3007) | `◯` (U+25EF)   | Repos                |

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

TODO: séparer explicitement les méthodes Hepburn et Kunrei (et Nippon-shiki ?)
TODO: décider du mode de représentation de 勺 en romaji (shaku, donc ambigu -> dshaku pour "down shaku" ?)

#### Kandokoro en chiffres romains vers kandokoro en kanji

Au sein des sections `tab::`, les kandokoro exprimés en chiffres romaji sont tolérés. C'est toutefois la forme en kanji qui est canonique. 

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

Au sein des sections `tab::`, les kandokoro étendus exprimés sous la forme d'un kanji composite sont tolérés. C'est toutefois la forme katakana + kanji qui est canonique.

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

Voir [notation musicale](notation.md) pour le détail des figures, modes rythmiques, suffixes de technique, positions étendues, positions hautes (préfixes イ/ロ), et options d'en-tête.
