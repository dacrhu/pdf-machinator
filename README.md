# PDF Machinator

Kisfunkciós PDF-korrektor asztali program (Linux / Windows / macOS): beleírás, megjegyzés, filc, karika.
A mentés az eredeti oldaltartalmat nem módosítja, a jegyzetek hozzáfűzve kerülnek a fájlba.

Repo: https://github.com/dacrhu/pdf-machinator · Licenc: AGPL-3.0 · Verzió: 1.0.0

## Futtatás
```
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/pdfmachinator
```
Teszt: `.venv/bin/pip install pytest && .venv/bin/python -m pytest`

## Licenc
GNU Affero General Public License v3.0 (lásd: LICENSE). A program a PyMuPDF-re (AGPL-3.0 / Artifex) épül,
ezért az egész projekt AGPL alatt áll: szabadon használható, módosítható és terjeszthető,
a módosított változatot azonos feltételekkel, forráskóddal együtt kell tovább adni.
