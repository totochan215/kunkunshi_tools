#!/usr/bin/env python3
"""kkml_cleaner.py — ancien nom de kkml_clean.py (shim de transition).

Émet un AVERTISSEMENT sur stderr, puis délègue à kkml_clean.py.
Utilisez plutôt : python3 kkml_clean.py ...
"""

import sys

import kkml_clean

if __name__ == "__main__":
    print(
        "kkml_cleaner: AVERTISSEMENT: ce script est renommé kkml_clean.py"
        " — exécutez plutôt `python3 kkml_clean.py ...`",
        file=sys.stderr,
    )
    sys.exit(kkml_clean.main())
