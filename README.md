# kunkunshi_tools

Outils de génération de tablatures 工工四 (kunkunshi) pour le sanshin d'Okinawa.
Python 3 autonome, aucune dépendance hors stdlib.

Pipeline : JSON Portama → KKML → SVG.

Réalisé en partie par intelligence artificielle (https://chat.mistral.ai/)

## Scripts

### portama2kkml.py

Convertit un export JSON de [Portama](https://portama.com/) en KKML.

    python3 portama2kkml.py input.json -o output.kkml
    cat input.json | python3 portama2kkml.py - > output.kkml

Gère : mapping PUA→kanji, accordages (本調子, 二揚げ, 三下げ etc.), ornements
(打ち音, uchi-utu etc.), paires main/straddle (noire, croche `A/B`, shuffle `A:B`),
repères de répétition `|:` `:|`, paroles (`::lyrics`).

### kkml2svg.py

Convertit un fichier KKML en tablature SVG. Layout vertical traditionnel
(cases lues de haut en bas, colonnes de droite à gauche) ou horizontal
(style songbook).

    python3 kkml2svg.py chanson.kkml -o chanson.svg
    python3 kkml2svg.py chanson.kkml                  # -> chanson.svg
    cat chanson.kkml | python3 kkml2svg.py -          # stdin -> stdout

Options CLI : `-o/--output`, `-c/--cols`, `-l/--layout vertical|horizontal`.

## Le format KKML

Format texte permettant de saisir et mettre en forme des tablatures 工工四 sous une forme intuitive.

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
    一、今日の誇らしゃや　何をにぎやなたてる　莟で居る花の　露行逢たごと
    ::

(Extrait de "Kajadifubushi")

- Métadonnées : `@title`, `@tuning`, `@cols`, `@layout`, `@marker`, `@author`,
  `@shaku_circled`, `@shaku_sharp`, `@end_circle`, `@lyrics_size`.
- Sections :
    - `::tab` — une ligne par dan, 1 token = 1 case. `A/B` = croche, `A:B` = shuffle,
      `|:` `:|` = répétitions, suffixes de technique `* ^ v < s =`.
    - `::vocal` — alignement approximatif du chant, 1 token = 1 syllabe,
      multi-caractères accolés (ぐゎ, てぃ, よー) possible, alignées note à note,
      rendues dans la colonne marker.
    - `::lyrics` — couplets en écriture horizontale, avec support du guide phonétique (ruby).

Détail complet : `docs/kkml-format.md` et `docs/notation.md`.

## Documentation

- `docs/kkml-format.md` — syntaxe et règles du format KKML
- `docs/notation.md` — notation musicale (positions, modes rythmiques, souhou, vocal)
- `docs/svg-layout.md` — layout SVG (dimensions, constantes, colonne marker)
- `docs/converter-architecture.md` — architecture des deux scripts
- `docs/portama-format.md` — description du format JSON Portama sur la base de sa rétro-ingénierie (PUA, allRubyData, géométrie mesurée des PDF)

## Echantillons de fichiers

- `samples/kkml/` — fichiers KKML de référence : かぎやで風節,
  だんじゅかりゆし, 国頭ジントヨー, fixture de test vocal
- `samples/portama-json/` — exports JSON Portama bruts (3 fichiers, dont かぎやで風節 avec allRubyData)
- `samples/portama-pdf/` — PDF Portama sources correspondant aux échantillons
- `samples/svg/` — rendus SVG de référence produits par kkml2svg (`python3 tests/run_tests.py --write-svg`)

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
