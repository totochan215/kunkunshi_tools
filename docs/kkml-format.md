# Format KKML (Kunkunshi Markup Language)

Le KKML est un format texte destiné à l'encodage des tablatures Kunkunshi. L'objectif est de proposer une alternative au format JSON de Portama, qui réponde aux deux défis suivants :
- Il doit être possible de saisir facilement la tablature à l'aide d'un éditeur de texte brut,
- Un musicien doit pouvoir exécuter le morceau en ayant le fichier KKML brut sous les yeux.

Par ailleurs, KKML tente de combler des manques inhérents au format JSON de Portama : support des positions de base manquantes, des positions hautes, de figures rythmiques non prises en charge, etc.

En développant KKML et ses outils, nous espérons rendre la génération de tablatures Kunkunshi accessile à tous !

## Format source

KKML se base sur le format texte brut encodé en UTF-8.

## Structure générale

```
# commentaire (ignoré)
@meta valeur
@cols 12

::tab
<tablature sous forme de cases représentant des temps et séparés par des espaces ; au sein de chaque case, tokens représentant des notes, leurs altérations et leur techniques de jeu>
::

::tab-lyrics
<paroles en phonétique, positionnées approximativement sur le rythme>
::

::lyrics
<paroles en texte libre, organisées par couplets>
::

::section titre optionnel
```

L'ordre des sections n'est pas imposé, toutefois dans une logique d'exécution du morceau en ayant le fichier KKML sous les yeux, il est recommandé de faire figurer la section tab:: en haut, juste sous les métadonnées.

Tolérance : si aucune section `::` n'est déclarée, les lignes hors métadonnées et commentaires sont considérées comme une section `::tab` implicite.

Tolérance de saisie (IME japonais, pleine chasse) — dans les blocs `::tab` et le côté positions de `::tab-lyrics`, les équivalents pleine chasse sont normalisés vers la forme canonique, avec une info sur stderr (une fois par variante) :

| Saisie acceptée | Converti en | Usage |
|---|---|---|
| `／` | `/` | croches, accords |
| `：` | `:` | shuffle |
| `｜` | `\|` | marques de répétition `\|:` / `:\|`, séparateur tab-lyrics |
| `＃` ou `#` | `♯` | altération (尺＃) |
| `＋` | `+` | accords (variante `+`, non encore rendue comme accord — roadmap) |
| `＊` `＾` `＜` `＝` | `*` `^` `<` `=` | suffixes de technique |
| `ー` `ｰ` `－` (token isolé) | `-` | case vide. Un ー collé à un kanji (ex. `中ー`) reste un token non reconnu : le chōonpu est une voyelle longue légitime dans `::vocal`/`::lyrics`, on ne devine pas l'intention |

Les espaces multiples et l'espace pleine chasse `　` (U+3000) sont de toute façon des séparateurs de tokens valides. La normalisation ne touche PAS les blocs `::vocal` et `::lyrics` (le ー y reste une voyelle longue).

## Métadonnées

- `@title` — titre de la chanson
- `@genre` — genre musical. Déprécié : sert de placeholder pour l'auteur lorsqu'il est connu.
- `@author` — auteur du morceau
- `@composer` — compositeur
- `@lyricist` — parolier
- `@origin` — origine
- `@tuning` — accordage relatif. Défaut : `本調子`. Valeurs connues : `本調子`, `二揚げ`, `三下げ`, `一二揚げ`, `一揚げ`.
- `@base_note` — note de base, correspondant à la hauteur de la position 合 (cas des accordages 本調子, 二揚げ et 三下げ) ou 合 moins 2 demi-tons (cas des accordages 一二揚げ et 一揚げ). Défaut : `C3`.
- `@layout vertical|horizontal` — indication de mise en forme lors du rendu (défaut : vertical)
- `@cols n` — nombre de cellules par dan (défaut : `12`)
- `@marker on|off` — active/désactive le marqueur (défaut : `on`)
- `@end_circle on|off` — indique si un symbole spécifique de fin de chanson doit être affiché.
- `@font_style mincho|gothic|serif` — style de police à utiliser pour le rendu (défaut : `mincho`). `mincho` = font-stack serif japonais (Hiragino Mincho ProN, YuMincho, MS PMincho, Noto Serif CJK JP), `gothic` = font-stack sans-serif japonais (Hiragino Kaku Gothic ProN, Yu Gothic, Meiryo, MS Gothic, Noto Sans CJK JP), serif = police serif générique (comportement historique). La police réelle dépend du système qui affiche le SVG.
- `@shaku_circled on|off` — rend les 尺 entourés d'un cercle (défaut : `on` ; `off` les rend sans cercle). 尺♯ n'est jamais rendu entouré. 下尺 est toujours rendu entouré. Dans les composés イ下尺 / ロ下尺, le 尺 n'est jamais rendu entouré.
- `@shaku_sharp on|off` — rend les 尺♯ avec le symbole ♯ (défaut : `on` ; `off` les rend comme 尺)
- `@lyrics_size small|medium|big` — taille de police des couplets : `small` = 50%, `medium` = 75%, `big` = 100% de la taille des kanjis de kunkunshi. Affecte la taille des caractères, l'espacement vertical, la largeur des colonnes de couplets, l'espacement entre colonnes, et la marge entre couplets et grille. Défaut : medium.
- `@ruby_size` — taille du ruby en pourcentage de la base (défaut : `50`). Réservé pour usage futur.
- `@musicno` — numéro de morceau (pour compatibilité Portama)
- `@chogen` — accordage absolu (pour compatibilité Portama)
- `@speed` — tempo (pour compatibilité Portama)
- `@rythm` - rythme (pour compatibilité Portama)
- `@rythm_mode` - mode_rythmique (pour compatibilité Portama)

Toutes les métadonnées sont optionnelles.

## Blocs

- `::tab` — bloc de tablature, chaque ligne = tokens séparés par des espaces
- `::lyrics` — bloc de paroles, lignes vides = séparateurs de couplets. Le caractère `|` en fin de ligne force un saut de colonne. `||` en fin de ligne force un saut de colonne et insère une colonne blanche avant le contenu suivant. Marqueurs de couplet reconnus en début de première ligne :
  - `⚫︎` `・` ou `、` — marqueur générique.
  - `一、` `二、` `三、` etc. — numéro de couplet (numéraux CJK + 、). 
  - `女　` ou `男　` — pour spécifier un couplet chanté par les femmes `女　` ou les hommes `男　` (kanji + espace full-width). 
    Plusieurs types de couplets peuvent être mélangés dans un même morceau.
- `::tab-lyrics` — paroles en phonétique alignées de manière approximative sur les temps de la tablature, format `positions | syllabes`. Souvent limité au premier couplet. Une ligne  plus courte que la ligne de tablature correspondante est complétée par des vides.
- `::vocal` — bloc de syllabes vocales. Chaque ligne correspond à la ligne de `::tab` de même index (le bloc doit suivre immédiatement un bloc `::tab`). Les syllabes sont séparées par des espaces ; 1 token = 1 syllabe. Un token peut faire plusieurs caractères pour les consonnes complexes de l'uchi-na-guchi (ぐゎ, くゎ, てぃ, でぃ, とぅ, づぅ…) ou les voyelles longues (よー) — les caractères d'une même syllabe sont accolés sans espace. Rendu dans la colonne marker à droite de la grille : caractère principal aligné sur la note, caractères combinants empilés en dessous. Une ligne vocale plus courte que la ligne de tab est complétée par des vides (alignement préservé, ex. intro uta-mochi).
- `::section label` — définit un titre de section (s'applique au bloc suivant)
- `::ruby` — PROPOSITION non implémentée (15 sept. 2026) : variante compatible Portama de `::vocal`, tokens préfixés par leur position en unités Portama (`26.5:きゆ 32.5:ぬ`, 1 unité = 1/3 de case, 0 = haut de la grille du dan, demi-unités autorisées).

`::` ferme le bloc courant.

## Ruby

Le ruby est un guide phonétique placé à droite du texte de base en écriture verticale, ou au-dessus en écriture horizontale. Il permet de préciser la lecture exacte des caractères, ce qui est particulièrement utile dans les langues Ryukyu (okinawaïennes) car ces lectures divergent fréquemment du japonais standard, y compris les lectures de Kana dans certains cas (ex. の généralement lu ぬ). En japonais standard, cela reste utile pour les musiciens peu à l'aise avec la lecture des Kanji, ou dans le cas des Kanji rares. 

Trois syntaxes sont possibles pour encoder les rubys en KKML :

| Syntaxe | Type | Description | Exemple |
|---------|------|-------------|---------|
| ` X《a》` | Mono-ruby | Le dernier caractère avant `《》` est la base | ` 安《あ》` → 安+あ |
| `｛XYZ｝《abc》` | Group-ruby | Le texte entre `｛｝` est la base groupée | `｛安里屋｝《あさとや》` → 安里屋+あさとや |
| `｛X《a》Y《b》｝` | Jukugo-ruby | Groupe avec annotations individuelles | `｛安《あ》里《さと》屋《や》｝` → 安+あ, 里+さと, 屋+や |

Détails :
- `《》` (U+300A / U+300B) = chevrons japonais doubles, délimitent l'annotation
- `｛｝` (U+FF5B / U+FF5D) = accolades pleine largeur, délimitent le groupe de base
- En mono-ruby sans `｛｝`, seul le caractère placé immédiatement avant `《》` est annoté. Le texte précédent est rendu sans ruby.
- Le ruby peut être utilisé dans les métadonnées `@title` `@author`, `@composer`, `@lyricist`, `@origin`, `@genre` ainsi que dans les blocs `::lyrics`. Il n'est pas utilisable pour les autres métadonnées et blocs. En particulier, `::tab` est basé sur une syntaxe qui ne doit pas être altérée,  et `::tab-lyrics` est par construction déjà écrit en phonétique.

## Cases de tablature

Chaque case de tablature correspond à un temps. Les tablatures Kunkunshi ignorent la notion de mesure (3/4, 1/2 etc.)

Séparateurs de tokens (à l'intérieur d'une case) :

| Séparateur | Mode                                    | Exemple              |
|------------|-----------------------------------------|----------------------|
| `/`        | Deux croches                            | `合/工`               |
| `:`        | Une croche pointée et une double croche | `合:工`               |
| `-`        | Accord (notes simultanées, max 3)       | `四-工` ou `合-四-工`  |
| (aucun)    | Position étendue                        | `下老`, `イ尺`, `尺♯`… |

Token non reconnu (ni position, ni séparateur, ex. `合工尺`) : le convertisseur émet une alerte sur stderr (une seule fois par token unique) et applique un rendu dégradé — les 3 premiers caractères au maximum, condensés en largeur comme `イ中` (2 caractères) ou `イ下尺` (3 caractères). L'ancien comportement « ornement » (empilement vertical de tous les caractères) est déprécié depuis le 19 sept. 2026 : il n'avait pas de sémantique musicale (les kanji empilés réels sont des croches `A/B`, du hayabiki `A:B` ou des accords `A-B`, chacun ayant son séparateur).

Voir [notation musicale](notation.md) pour le détail des tokens, modes rythmiques, suffixes de technique, positions étendues, positions hautes (préfixes イ/ロ, dont イ下尺/ロ下尺), et options d'en-tête.
