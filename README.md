# kunkunshi_tools

Outils de génération de tablatures 工工四 (kunkunshi) pour le sanshin d'Okinawa.
Python 3 autonome, aucune dépendance hors stdlib.

Pipeline : JSON Portama → KKML → SVG.

Réalisé en partie par intelligence artificielle (https://chat.mistral.ai/)

## Scripts

### portama2kkml.py

Convertit un export JSON de [Portama](https://portama.com/) (page d'accueil ; [éditeur de kunkunshi](https://portama.com/editor)) en KKML.

    python3 portama2kkml.py input.json -o output.kkml
    cat input.json | python3 portama2kkml.py - > output.kkml

Gère : mapping PUA→kanji, accordages (本調子, 二調子, 三調子), ornements
(uchi-utu), paires main/straddle (noire, croche `A/B`, shuffle `A:B`),
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
    ::

- En-têtes : `@title`, `@tuning`, `@cols`, `@layout`, `@marker`, `@author`,
  `@shaku_circled`, `@shaku_sharp`, `@end_circle`, `@lyrics_size`.
- `::tab` — une ligne par dan, 1 token = 1 case. `A/B` = croche, `A:B` = shuffle,
  `|:` `:|` = répétitions, suffixes de technique `* ^ v < s =`.
- `::vocal` — syllabes vocales (uchi-na-guchi), 1 token = 1 syllabe,
  multi-caractères accolés (ぐゎ, てぃ, よー), alignées note à note,
  rendues dans la colonne marker.
- `::lyrics` — couplets en écriture horizontale, ruby `《》` supporté.

Détail complet : `docs/kkml-format.md` et `docs/notation.md`.

## Documentation

- `docs/kkml-format.md` — syntaxe et règles du format KKML
- `docs/notation.md` — notation musicale (positions, modes rythmiques, souhou, vocal)
- `docs/svg-layout.md` — layout SVG (dimensions, constantes, colonne marker)
- `docs/converter-architecture.md` — architecture des deux scripts
- `docs/portama-format.md` — format JSON Portama (PUA, allRubyData, géométrie mesurée des PDF)

## Contenu

- `songs/` — fichiers KKML de référence : かぎやで風節 (avec et sans `::vocal`),
  だんじゅかりゆし, 国頭ジントヨー, fixture de test vocal
- `samples/` — exports JSON Portama bruts (3 fichiers, dont かぎやで風節 avec allRubyData)
