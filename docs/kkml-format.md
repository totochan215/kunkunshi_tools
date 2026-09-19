# Format KKML (Kunkunshi Markup Language)

Le KKML est un format texte simple pour encoder des tablatures de sanshin okinawaïen.

## Structure générale

```
# commentaire (ignoré)
@meta valeur
@cols 12

::tab
<tokens séparés par espaces>
::

::lyrics
<paroles, lignes vides = séparateurs de couplets>
::

::tab-lyrics
positions | syllabes
::

::section titre optionnel
```

## Métadonnées reconnues

- `@title` — titre de la chanson (rendu verticalement à droite de la grille en mode vertical). Défaut : vide (aucun titre affiché)
- `@tuning` — accordage (rendu verticalement sous le titre). Défaut : `本調子`. Toute valeur est acceptée et affichée telle quelle (connues : `本調子`, `二揚げ`, `三下げ`) ; le mapping des accordages côté import Portama est fait par portama2kkml.py
- `@genre` — genre musical (rendu dans l'en-tête). Déprécié : sert de placeholder pour l'auteur lorsqu'il est connu. Si vide/non spécifié, non affiché.
- `@author` — auteur de la chanson (rendu sous le genre). Défaut : vide (non affiché). Si l'auteur est strictement égal au genre, seul l'auteur est affiché.
- `@end_circle on|off` — ajoute un marqueur de fin de chanson dans la colonne marker : même géométrie que la flèche montante de boucle, mais avec un cercle creux (diamètre = base du triangle) au lieu d'un triangle. Positionné au bas de la dernière case remplie. Défaut : on (`off` pour désactiver). En mode vertical, ne s'affiche que si une colonne marker existe (`@marker on` ou bloc `::vocal`). Note pour le futur support multi-pages : le cercle ne devra apparaître que sur la dernière page, pas en bas de chaque page.
- `@lyrics_size small|medium|big` — taille de police des couplets : small = 50%, medium = 75%, big = 100% de la taille des kanjis de kunkunshi. Affecte la taille des caractères, l'espacement vertical, la largeur des colonnes de couplets, l'espacement entre colonnes, et la marge entre couplets et grille. Défaut : medium.
- `@ruby_size` — taille du ruby en pourcentage de la base (défaut : 50). Réservé pour usage futur.

## Ruby (guide phonétique)

Le ruby est un guide phonétique placé à droite du texte de base en écriture verticale, au-dessus en écriture horizontale. Taille = 50% de la base, contact cadre-à-cadre (pas d'interstice). Le bloc ruby est centré sur le bloc base.

Trois syntaxes :

| Syntaxe | Type | Description | Exemple |
|---------|------|-------------|---------|
| `X《y》` | Mono-ruby | Le dernier caractère avant `《》` est la base | `安《あ》` → 安 + あ |
| `｛XYZ｝《abc》` | Group-ruby | Le texte entre `｛｝` est la base groupée | `｛安里屋｝《あさとや》` → 安里屋 + あさとや |
| `｛X《a》Y《b》｝` | Jukugo-ruby | Groupe avec annotations individuelles | `｛安《あ》里《さ》屋《や》｝` |

Détails :
- `《》` (U+300A / U+300B) = chevrons japonais doubles, délimitent l'annotation
- `｛｝` (U+FF5B / U+FF5D) = accolades pleine largeur, délimitent le groupe de base
- En mono-ruby sans `｛｝`, seul le caractère immédiatement avant `《》` est annoté. Le texte précédent est rendu sans ruby.
- Le ruby s'applique au `@title` et aux blocs `::lyrics`. Pas applicable à `@tuning`, `@author`, `@genre`, ni aux blocs `::tab` / `::tab-lyrics`.
- `@composer` — compositeur (en-tête)
- `@lyricist` — parolier (en-tête)
- `@origin` — origine (en-tête)
- `@marker on|off` — active/désactive la colonne de marqueur à droite de chaque pile
- `@cols N` — nombre de lignes par colonne en mode vertical (défaut : 12)
- `@layout vertical|horizontal` — force le layout
- `@font_style mincho|gothic|serif` — style de police japonais (défaut : serif, comportement historique). mincho = font-stack serif japonais (Hiragino Mincho ProN, YuMincho, MS PMincho, Noto Serif CJK JP), gothic = font-stack sans-serif japonais (Hiragino Kaku Gothic ProN, Yu Gothic, Meiryo, MS Gothic, Noto Sans CJK JP). La police réelle dépend du système qui affiche le SVG.
- `@shaku_circled on|off` — rend les 尺 en 尺 entourés d'un cercle (défaut : off). S'applique aux 尺 dans les noires ET dans les croches (note principale ou note à cheval). 尺♯ n'est jamais entouré. 下尺 est toujours entouré. Dans les composés イ下尺 / ロ下尺, le 尺 n'est pas entouré : les 3 caractères sont rendus condensés.
- `@shaku_sharp on|off` — rend les 尺♯ avec le symbole ♯ (défaut : on ; `off` les rend comme 尺)

## Blocs

- `::tab` — bloc de tablature, chaque ligne = tokens séparés par des espaces
- `::lyrics` — bloc de paroles, lignes vides = séparateurs de couplets. Le caractère `|` en fin de ligne force un saut de colonne. `||` en fin de ligne force un saut de colonne et insère une colonne blanche avant le contenu suivant. Marqueurs de couplet reconnus en début de première ligne :
  - `一、` `二、` etc. — numéro de couplet (numéraux CJK + 、). Indentation du reste du couplet sous le 、.
  - `⚫︎` ou `・` — marqueur générique (1 caractère + variation selector optionnel). Indentation sous le caractère suivant.
  - `女　` ou `男　` — couplet chanté par les femmes / les hommes (kanji + espace full-width). Indentation sous l'espace. Les types de couplets peuvent être mélangés.
- `::tab-lyrics` — tablature avec syllabes alignées, format `positions | syllabes`
- `::vocal` — bloc de syllabes vocales. Chaque ligne correspond à la ligne de `::tab` de même index (le bloc doit suivre immédiatement un bloc `::tab`). Les syllabes sont séparées par des espaces ; 1 token = 1 syllabe. Un token peut faire plusieurs caractères pour les consonnes complexes de l'uchi-na-guchi (ぐゎ, くゎ, てぃ, でぃ, とぅ, づぅ…) ou les voyelles longues (よー) — les caractères d'une même syllabe sont accolés sans espace. Rendu dans la colonne marker à droite de la grille : caractère principal aligné sur la note, caractères combinants empilés en dessous. Une ligne vocale plus courte que la ligne de tab est complétée par des vides (alignement préservé, ex. intro uta-mochi).
- `::` — ferme le bloc courant
- `::section label` — définit un titre de section (s'applique au bloc suivant)
- `::ruby` — PROPOSITION non implémentée (15 sept. 2026) : variante compatible Portama de `::vocal`, tokens préfixés par leur position en unités Portama (`26.5:きゆ 32.5:ぬ`, 1 unité = 1/3 de case, 0 = haut de la grille du dan, demi-unités autorisées).

## Tokens de tablature

Séparateurs de token (à l'intérieur d'un token) :

| Séparateur | Mode | Exemple |
|------------|------|---------|
| `/` | Croche (note principale + note à cheval) | `合/工` |
| `:` | Shuffle 早弾き (deux notes égales empilées) | `合:工` |
| `-` | Accord (notes simultanées, max 3) | `四-五` ou `合-工-尺` |
| (aucun) | Ornement (caractères empilés) ou position étendue | `合工尺`, `下老`, `イ尺` |

Voir [notation musicale](notation.md) pour le détail des tokens, modes rythmiques, suffixes de technique, positions étendues, positions hautes (préfixes イ/ロ, dont イ下尺/ロ下尺), et options d'en-tête.
