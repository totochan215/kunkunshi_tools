# Samples

Echantillons de fichiers.

### Homologues et tests

- Les fichiers échantillons portant le même nom de base (sans suffixe) à travers `samples/kkml`,
`samples/portama-json`, `samples/portama-pdf` et `samples/svg` sont des
homologues : ils représentent la même chanson et peuvent donc être utilisés pour des tests.
- Un suffixe de variante après
`-` distingue des variantes (ex. `かぎやで風節-vocal.kkml`). Les segments ruby
entre crochets éventuels sont ignorés dans l'appariement (`国頭[くんじゃん]ジントヨー.pdf`
correspond à `国頭ジントヨー.kkml`).

### Forme canonique

- Les fichiers de `samples/kkml/` sont en **forme canonique** : ils ont été
  passés au cleaner (`python3 kkml_clean.py`), qui est idempotent. Ils sont
  présentables tels quels.
- Les versions « sales » d'origine sont conservées comme fixtures de test
  dans [tests/fixtures/dirty/](../tests/fixtures/dirty/).
- `samples/kkml/` ne contient que des **chansons/medleys réels**. Les fichiers
  synthétiques de test (`テスト節.kkml`, `テスト節-2.kkml`, `medley-samples.kkml`,
  avec les rendus mega de référence `medley-samples-mega-p1/p2.svg`) sont dans
  [tests/fixtures/synthetic/](../tests/fixtures/synthetic/).
