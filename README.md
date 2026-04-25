# Prediction de la participation aux municipales 2032

## Objectif
Ce projet fournit une base de travail complete pour :

- comparer les municipales 2014, 2020 et 2026 a l'echelle communale ;
- mettre en evidence l'anomalie de 2020 dans le contexte Covid-19 ;
- analyser des facteurs explicatifs de la participation ;
- preparer un dataset propre pour une future prediction du nombre de votants et du taux de participation en 2032.

Le projet est pense pour une soutenance academique : code modulaire, visualisations lisibles, commentaires explicatifs et traitement defensif des colonnes heterogenes.

## Arborescence
```text
Data prediction/
|-- analysis_municipales_2032.ipynb
|-- README.md
|-- dataset_final.csv                  # Genere par le notebook
|-- data/
|   |-- elections_2014.csv
|   |-- elections_2020.csv
|   |-- elections_2026.csv
|   |-- population.csv
|   |-- chomage.csv
|   |-- revenus_pauvrete.csv
|   '-- crimes_delits.csv
|-- outputs/
|   '-- figures/
'-- src/
    |-- __init__.py
    |-- load_data.py
    |-- preprocess.py
    |-- visualize.py
    '-- model.py
```

## Fichiers attendus
Place les CSV suivants dans le dossier `data/` :

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

## Execution
1. Deposer les donnees dans `data/`.
2. Ouvrir le notebook :

```bash
jupyter notebook analysis_municipales_2032.ipynb
```

3. Executer les cellules dans l'ordre.

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

## Strategie de robustesse
Le code a ete ecrit pour resister a des fichiers reels souvent heterogenes :

- detection souple des colonnes de type `code_commune`, `nom_commune`, `inscrits`, `votants`, etc. ;
- chargement tolerant a plusieurs encodages et separateurs ;
- gestion des doublons ;
- conversion defensive des colonnes numeriques ;
- jointures non bloquantes si une colonne attendue est absente ;
- prise en compte explicite de `covid_2020` pour eviter de traiter 2020 comme une simple tendance lineaire.

## Limites de l'approche
- Les resultats dependent fortement de la qualite et de la granularite des CSV telecharges.
- La projection 2032 est exploratoire : elle prolonge le dernier contexte observe, sans scenario macroeconomique futur detaille.
- Avec seulement trois elections municipales, les modeles sont utiles pour preparer l'analyse predictive, mais pas pour conclure seuls sur une prevision definitive.

## Pistes d'amelioration
- ajouter des variables territoriales fines ;
- integrer des projections INSEE futures ;
- construire des modeles par segment de communes ;
- tester une validation temporelle plus stricte quand davantage d'historique sera disponible.
