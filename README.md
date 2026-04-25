# MsprData

Analyse exploratoire des elections municipales 2014, 2020 et 2026, avec une base de travail pour preparer une prediction de la participation aux municipales 2032.

## Analyses disponibles

- `eda_municipales_2014_2020_2026.py` : script d'analyse exploratoire a partir de `general_results.csv`
- `rapport_eda_municipales.md` : synthese des constats et pistes de problematique
- `analysis_municipales_2032.ipynb` : notebook de preparation du dataset final et de projection exploratoire 2032
- `src/` : fonctions modulaires de chargement, preprocessing, visualisation et modelisation
- `outputs/` : exports CSV et figures produits par les analyses

## Donnees source

Le fichier brut `general_results.csv` n'est pas versionne dans ce depot car GitHub limite les fichiers a 100 MB.

- Source directe : <https://object.files.data.gouv.fr/data-pipeline-open/elections/general_results.csv>
- Page officielle : <https://www.data.gouv.fr/datasets/donnees-des-elections-agregees/>

Place simplement `general_results.csv` a la racine du projet avant l'execution du script EDA.

Le notebook de prediction utilise aussi les fichiers prepares dans `data/` :

- `data/elections_2014.csv`
- `data/elections_2020.csv`
- `data/elections_2026.csv`
- `data/population.csv`
- `data/chomage.csv`
- `data/revenus_pauvrete.csv`
- `data/crimes_delits.csv`

## Installation conseillee

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy matplotlib seaborn scikit-learn scipy jupyter
```

## Lancer l'analyse EDA

```bash
python3 eda_municipales_2014_2020_2026.py
```

Les sorties sont ecrites dans `outputs/`.

## Lancer le notebook de prediction

```bash
jupyter notebook analysis_municipales_2032.ipynb
```

Le notebook :

- charge les donnees ;
- inspecte et harmonise les colonnes ;
- calcule les variables electorales utiles ;
- fusionne les sources contextuelles ;
- produit les graphiques dans `outputs/figures/` ;
- exporte `dataset_final.csv` ;
- prepare un jeu de donnees machine learning ;
- compare plusieurs approches de prise en compte de 2020 ;
- propose une projection exploratoire 2032.

## Limites de l'approche predictive

- Les resultats dependent fortement de la qualite et de la granularite des CSV telecharges.
- La projection 2032 est exploratoire : elle prolonge le dernier contexte observe, sans scenario macroeconomique futur detaille.
- Avec seulement trois elections municipales, les modeles sont utiles pour preparer l'analyse predictive, mais pas pour conclure seuls sur une prevision definitive.
