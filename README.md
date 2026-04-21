# MsprData

Analyse exploratoire des elections municipales 2014, 2020 et 2026 a partir du fichier agrege `general_results.csv`.

## Fichiers principaux

- `eda_municipales_2014_2020_2026.py` : script d'analyse exploratoire
- `rapport_eda_municipales.md` : synthese des constats et pistes de problematique
- `outputs/` : exports CSV et figures produits par le script

## Donnees source

Le fichier brut `general_results.csv` n'est pas versionne dans ce depot car GitHub limite les fichiers a 100 MB.

- Source directe : <https://object.files.data.gouv.fr/data-pipeline-open/elections/general_results.csv>
- Page officielle : <https://www.data.gouv.fr/datasets/donnees-des-elections-agregees/>

Place simplement `general_results.csv` a la racine du projet avant l'execution du script.

## Lancer l'analyse

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas matplotlib seaborn
python3 eda_municipales_2014_2020_2026.py
```

Les sorties sont ecrites dans `outputs/`.
