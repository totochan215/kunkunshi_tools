# Format KKML (Kunkunshi Markup Language)

Le KKML est un format texte simple pour encoder des tablatures de sanshin d'Okinawa. L'objectif est de proposer une alternative au format JSON de Portama, qui permette une approche visuelle : un musicien doit pouvoir exécuter le morceau en ayant le fichier KKML brut sous les yeux.
Par ailleurs, KKML tente de combler des manques inhérents au format JSON de Portama, par exemple des positions manquantes, etc.

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

Tolérance (section implicite) : si aucune section `::` n'est déclarée, les lignes hors en-tête (métadonnées) et commentaire sont traitées comme une section `::tab` implicite.

## Métadonnées reconnues

- `@title` — titre de la chanson. Défaut : vide.
- `@genre` — genre musical. Déprécié : sert de placeholder pour l'auteur lorsqu'il est connu.
- `@author` — auteur du morceau. Défaut : vide.
- `@composer` — compositeur
- `@lyricist` — parolier
- `@origin` — origine
- `@tuning` — accordage relatif. Défaut : `本調子`. Toute valeur est acceptée (valeurs connues : `本調子`, `二揚げ`, `三下げ`, `一二揚げ`, `一揚げ`)
- `@base_note` — note de base, correspondant à la hauteur de la position 合 (accordages 本調子, 二揚げ et 三下げ) ou 合 moins 2 demi-tons (accordages 一二揚げ et 一揚げ). Défaut : `C3`.
- `@layout vertical|horizontal` — force le layout (défaut : vertical)
- `@cols n` — nombre de lignes par colonne en mode vertical (défaut : `12`)
- `@marker on|off` — active/désactive la colonne de marqueur à droite de chaque pile (défaut : `on`)
- `@end_circle on|off` — indique si un marqueur spécifique de fin de chanson doit être affiché.
- `@font_style mincho|gothic|serif` — style de police à utiliser pour le rendu (défaut : `mincho`). `mincho` = font-stack serif japonais (Hiragino Mincho ProN, YuMincho, MS PMincho, Noto Serif CJK JP), `gothic` = font-stack sans-serif japonais (Hiragino Kaku Gothic ProN, Yu Gothic, Meiryo, MS Gothic, Noto Sans CJK JP), serif = police serif générique (comportement historique). La police réelle dépend du système qui affiche le SVG.
- `@shaku_circled on|off` — rend les 尺 en 尺 entourés d'un cercle (défaut : `on` ; `off` les rend sans cercle). S'applique aux 尺 dans les noires ET dans les croches (note principale ou note à cheval). 尺♯ n'est jamais entouré. 下尺 est toujours entouré. Dans les composés イ下尺 / ロ下尺, le 尺 n'est pas entouré : les 3 caractères sont rendus condensés.
- `@shaku_sharp on|off` — rend les 尺♯ avec le symbole ♯ (défaut : on ; `off` les rend comme 尺)
- `@lyrics_size small|medium|big` — taille de police des couplets : `small` = 50%, `medium` = 75%, `big` = 100% de la taille des kanjis de kunkunshi. Affecte la taille des caractères, l'espacement vertical, la largeur des colonnes de couplets, l'espacement entre colonnes, et la marge entre couplets et grille. Défaut : medium.
- `@ruby_size` — taille du ruby en pourcentage de la base (défaut : `50`). Réservé pour usage futur.

Toutes les métadonnées sont optionnelles.

## Ruby

Le ruby est un guide phonétique placé à droite du texte de base en écriture verticale, ou au-dessus en écriture horizontale. Il permet de préciser la lecture exacte des caractères, ce qui est particulièrement utile dans les langues Ryukyu (okinawaïennes) car ces lectures divergent fréquemment du japonais standard. 

Trois syntaxes sont possibles, selon l'emploi, pour encoder les rubys en KKML :

| Syntaxe | Type | Description | Exemple |
|---------|------|-------------|---------|
| ` X《a》` | Mono-ruby | Le dernier caractère avant `《》` est la base | `安《あ》` → 安+あ |
| `｛XYZ｝《abc》` | Group-ruby | Le texte entre `｛｝` est la base groupée | `｛安里屋｝《あさとや》` → 安里屋+あさとや |
| `｛X《a》Y《b》｝` | Jukugo-ruby | Groupe avec annotations individuelles | `｛安《あ》里《さと》屋《や》｝` → 安+あ, 里+さと, 屋+や |

Détails :
- `《》` (U+300A / U+300B) = chevrons japonais doubles, délimitent l'annotation
- `｛｝` (U+FF5B / U+FF5D) = accolades pleine largeur, délimitent le groupe de base
- En mono-ruby sans `｛｝`, seul le caractère immédiatement avant `《》` est annoté. Le texte précédent est rendu sans ruby.
- Le ruby s'applique aux métadonnées `@title` `@author`, `@genre` et aux blocs `::lyrics`. Il n'est pas applicable à `@tuning` ni aux blocs `::tab` et `::tab-lyrics`.

## Blocs

- `::tab` — bloc de tablature, chaque ligne = tokens séparés par des espaces
- `::lyrics` — bloc de paroles, lignes vides = séparateurs de couplets. Le caractère `|` en fin de ligne force un saut de colonne. `||` en fin de ligne force un saut de colonne et insère une colonne blanche avant le contenu suivant. Marqueurs de couplet reconnus en début de première ligne :
  - `一、` `二、` `三、` etc. — numéro de couplet (numéraux CJK + 、). 
  - `⚫︎` `・` ou `、` — marqueur générique.
  - `女　` ou `男　` — pour spécifier un couplet chanté par les femmes ou les hommes (kanji + espace full-width). 
    Les types de couplets peuvent être mélangés dans un même morceau.
- `::tab-lyrics` — tablature avec syllabes alignées, format `positions | syllabes`
- `::vocal` — bloc de syllabes vocales. Chaque ligne correspond à la ligne de `::tab` de même index (le bloc doit suivre immédiatement un bloc `::tab`). Les syllabes sont séparées par des espaces ; 1 token = 1 syllabe. Un token peut faire plusieurs caractères pour les consonnes complexes de l'uchi-na-guchi (ぐゎ, くゎ, てぃ, でぃ, とぅ, づぅ…) ou les voyelles longues (よー) — les caractères d'une même syllabe sont accolés sans espace. Rendu dans la colonne marker à droite de la grille : caractère principal aligné sur la note, caractères combinants empilés en dessous. Une ligne vocale plus courte que la ligne de tab est complétée par des vides (alignement préservé, ex. intro uta-mochi).
- `::section label` — définit un titre de section (s'applique au bloc suivant)
- `::ruby` — PROPOSITION non implémentée (15 sept. 2026) : variante compatible Portama de `::vocal`, tokens préfixés par leur position en unités Portama (`26.5:きゆ 32.5:ぬ`, 1 unité = 1/3 de case, 0 = haut de la grille du dan, demi-unités autorisées).

`::` ferme le bloc courant.

## Tokens de tablature

Séparateurs de token (à l'intérieur d'un token) :

| Séparateur | Mode | Exemple |
|------------|------|---------|
| `/` | Deux croches | `合/工` |
| `:` | Une croche pointée et une double croche (早弾き) | `合:工` |
| `-` | Accord (notes simultanées, max 3) | `四-工` ou `合-四-工` |
| (aucun) | Position étendue | `下老`, `イ尺`, `尺♯`… |

Token non reconnu (ni position, ni séparateur, ex. `合工尺`) : le convertisseur émet une alerte sur stderr (une seule fois par token unique) et applique un rendu dégradé — les 3 premiers caractères au maximum, condensés en largeur comme `イ中` (2 caractères) ou `イ下尺` (3 caractères). L'ancien comportement « ornement » (empilement vertical de tous les caractères) est déprécié depuis le 19 sept. 2026 : il n'avait pas de sémantique musicale (les kanji empilés réels sont des croches `A/B`, du hayabiki `A:B` ou des accords `A-B`, chacun ayant son séparateur).

Voir [notation musicale](notation.md) pour le détail des tokens, modes rythmiques, suffixes de technique, positions étendues, positions hautes (préfixes イ/ロ, dont イ下尺/ロ下尺), et options d'en-tête.
