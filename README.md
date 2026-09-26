# kunkunshi_tools

Outils de génération de tablatures 工工四 (kunkunshi) pour le sanshin d'Okinawa.
Python 3 autonome, aucune dépendance hors stdlib.
En bref, un outil pour sanshin 🪕 sous python 🐍 ! 😂

- Pipeline 1 : saisie dans l'éditeur Portama → JSON Portama → KKML → retouche manuelle en KKML → SVG
- Pipeline 2 : saisie manuelle en KKML → SVG

Réalisé en (grande) partie par intelligence artificielle (https://chat.mistral.ai/)

## Scripts

### portama2kkml.py

Convertit un fichier JSON de [Portama](https://portama.com/) en KKML.

    python3 portama2kkml.py input.json -o output.kkml
    cat input.json | python3 portama2kkml.py - > output.kkml

Gère : mapping PUA → Kanji, accordages (本調子, 二揚げ, 三下げ etc.), ornements
(uchi-utu, kaki-utu etc.), paires main/straddle (noire, deux croches `A/B`, shuffle `A:B`),
repères de répétition `|:` `:|` `|(` `)|`, paroles (`::lyrics`).

### kkml2svg.py

Rend un fichier KKML sous forme de tablature SVG, en appliquant des options de layouting.

    python3 kkml2svg.py chanson.kkml -o chanson.svg
    python3 kkml2svg.py chanson.kkml                  # -> chanson.svg
    cat chanson.kkml | python3 kkml2svg.py -          # stdin -> stdout

Options CLI : `-o/--output`, `-c/--cols`, `-l/--layout vertical|horizontal`.

## Le format KKML

Format texte permettant de saisir et mettre en forme des tablatures 工工四 (kunkunshi) sous une forme simple et intuitive. KKML pour Kunkunshi Markup Language. Et si ça marche pas, c'est 💩

Exemple :

    @title かぎやで風節
    @tuning 本調子
    @cols 12

    ::tab
    |:工 五 四 工 四 乙 四 合/尺:| 工 ◯ 工 五
    工 尺♯ 工 合/尺♯ 工 五 工 尺♯ 工 合/尺♯ 工 五
    工 尺♯/工 上 尺* 上 老/四 上 尺♯ 上 老 四 老
    ::

    ::vocal
    - - - - - - - - きゆ - ぬ -
    - ふ - - - - く - - - ら -
    しゃ - - - - - - - や - - -
    ::

    ::lyrics
    一、｛今日｝《きゆ》の《ぬ》誇《ふく》らしゃや　何をにぎやなたてる　莟で居る花の　露行逢たごと
    ::

(Extrait de かぎやで風節 (Kajadifu bushi))

- Métadonnées : `@title`, `@tuning`, `@cols`, `@layout`, `@marker`, `@author`,
  `@shaku_circled`, `@shaku_sharp`, `@end_circle`, `@lyrics_size`.
- Sections :
    - `::tab` — tablature, une ligne par dan, 1 token = 1 case. `A` = 1 noire, `A/B` = 2 croches, `A:B` = shuffle,
      `|:` `:|` = répétitions, suffixes de technique `* ^ v < s =`.
    - `::vocal` — alignement approximatif du chant, 1 token = 1 case correspondante au cases de ::tab,
    - `::lyrics` — couplets avec support du guide phonétique (ruby).

Détail complet : `docs/kkml-format.md` et `docs/notation.md`.

## Documentation

- `docs/converter-architecture.md` — architecture des deux scripts
- `docs/kkml-format.md` — syntaxe et règles du format KKML
- `docs/notation.md` — notation musicale (positions, modes rythmiques, souhou, vocal)
- `docs/portama-format.md` — description du format JSON Portama sur la base de sa rétro-ingénierie (PUA, allRubyData, géométrie mesurée des PDF)
- `docs/svg-layout.md` — layout SVG (dimensions, constantes, colonne marker)

## Echantillons de fichiers

- `samples/kkml/` — fichiers KKML de référence
- `samples/portama-json/` — fichiers JSON Portama bruts
- `samples/portama-pdf/` — fichiers Portama rendus au format PDF
- `samples/svg/` — rendus SVG de référence produits par kkml2svg

## Homologues et tests

Des fichiers portant le même nom de base (sans suffixe) à travers `samples/kkml`,
`samples/portama-json`, `samples/portama-pdf` et `samples/svg` sont des
homologues : ils représentent la même chanson. Un suffixe de variante après
`-` distingue les variantes (ex. `かぎやで風節-vocal.kkml`). Les segments ruby
entre crochets sont ignorés dans l'appariement (`国頭[くんじゃん]ジントヨー.pdf`
correspond à `国頭ジントヨー.kkml`).

`python3 tests/run_tests.py` détecte les homologues et rend chaque `.kkml`
(vertical + horizontal) : échec si kkml2svg sort non-zéro ou émet un
AVERTISSEMENT. `--write-svg` écrit en plus les rendus dans `samples/svg/`.
