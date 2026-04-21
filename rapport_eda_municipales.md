# Analyse exploratoire des municipales 2014, 2020 et 2026

Source principale analysée :
- Fichier CSV : `general_results.csv`
- URL source : <https://object.files.data.gouv.fr/data-pipeline-open/elections/general_results.csv>
- Page officielle : <https://www.data.gouv.fr/datasets/donnees-des-elections-agregees/>

## 1. Résumé du dataset

- Dimensions du fichier complet : `3 162 440` lignes et `25` colonnes.
- Le fichier contient `56` identifiants d'élection distincts dans une table unique.
- Les identifiants municipaux présents sont :
  - `2008_muni_t1`
  - `2008_muni_t2`
  - `2014_muni_t1`
  - `2014_muni_t2`
  - `2020_muni_t1`
  - `2020_muni_t2`
  - `2026_muni_t1`
  - `2026_muni_t2`
- Les identifiants à retenir pour ce projet sont bien :
  - `2014_muni_t1`, `2014_muni_t2`
  - `2020_muni_t1`, `2020_muni_t2`
  - `2026_muni_t1`, `2026_muni_t2`

Sous-ensemble municipal 2014/2020/2026 :
- `266 585` lignes.

Répartition des lignes :
- `2014_muni_t1` : `68 169`
- `2014_muni_t2` : `22 480`
- `2020_muni_t1` : `68 941`
- `2020_muni_t2` : `19 594`
- `2026_muni_t1` : `70 003`
- `2026_muni_t2` : `17 398`

## 2. Structure et qualité des données

Colonnes présentes :
- `id_election`
- `id_brut_miom`
- `code_departement`, `libelle_departement`
- `code_canton`, `libelle_canton`
- `code_commune`, `libelle_commune`
- `code_circonscription`, `libelle_circonscription`
- `code_bv`
- `inscrits`, `abstentions`, `votants`, `blancs`, `nuls`, `exprimes`
- `ratio_abstentions_inscrits`, `ratio_votants_inscrits`
- `ratio_blancs_inscrits`, `ratio_blancs_votants`
- `ratio_nuls_inscrits`, `ratio_nuls_votants`
- `ratio_exprimes_inscrits`, `ratio_exprimes_votants`

Constats de structure :
- La structure est commune à plusieurs élections, donc certaines colonnes sont vides selon le type de scrutin.
- Pour les municipales 2014/2020/2026, les colonnes `code_canton`, `libelle_canton`, `code_circonscription` et `libelle_circonscription` sont entièrement vides.
- Le schéma de colonnes reste stable entre 2014, 2020 et 2026 dans le fichier actuel.
- En revanche, la complétude des variables change selon les années.

Valeurs manquantes marquantes sur le sous-ensemble municipal :
- `blancs` : `90 649` valeurs manquantes, soit `34,0 %`
- `ratio_blancs_inscrits` : `34,0 %`
- `ratio_blancs_votants` : `34,0 %`

Interprétation correcte :
- ces manques correspondent aux municipales 2014, où la variable `blancs` n'est pas renseignée dans ce fichier.

Doublons :
- `0` doublon exact sur le fichier complet.

Anomalies :
- `7` lignes avec valeurs négatives, toutes sur les municipales 2026.
- `101` lignes avec `inscrits = 0` ou `votants = 0`, presque toutes en 2026.
- Les égalités comptables `inscrits = abstentions + votants` tiennent sur `100 %` des lignes municipales.
- Les égalités `votants = exprimes + nuls + blancs` tiennent sur 2020 et 2026, mais pas sur 2014 car `blancs` est absent.

Point de vigilance :
- `libelle_commune` n'est pas assez stable pour les jointures temporelles.
- Il faut utiliser `code_commune` et non le libellé pour comparer les années.

## 3. Identification des élections 2014 / 2020 / 2026

Les identifiants exacts trouvés dans `id_election` sont :
- `2014_muni_t1`
- `2014_muni_t2`
- `2020_muni_t1`
- `2020_muni_t2`
- `2026_muni_t1`
- `2026_muni_t2`

Conclusion :
- il ne faut pas chercher trois fichiers séparés.
- Les trois millésimes sont bien stockés dans la même table et doivent être filtrés par `id_election`.

## 4. Variables exploitables

Variables directement exploitables :
- volume électoral : `inscrits`, `votants`, `exprimes`
- non-participation : `abstentions`
- votes non exprimés : `blancs`, `nuls`
- ratios déjà calculés : participation, abstention, blancs, nuls, exprimés
- géographie : `code_departement`, `libelle_departement`, `code_commune`, `libelle_commune`, `code_bv`
- identifiants techniques : `id_election`, `id_brut_miom`

Variables peu utiles ici :
- `code_canton`, `libelle_canton`
- `code_circonscription`, `libelle_circonscription`

Limite importante :
- Ce fichier ne contient pas les résultats par candidat ou par liste.
- On ne peut donc pas étudier avec ce seul dataset les rapports de force partisans, les scores de listes, les alternances politiques ou la fragmentation de l'offre électorale.

## 5. Niveau géographique exploitable

Niveau le plus fin réellement disponible :
- la ligne est au niveau bureau de vote.

Mais le niveau est hétérogène en pratique :
- certaines communes n'ont qu'une seule ligne, souvent avec `code_bv = 0001`
- d'autres communes ont plusieurs lignes, une par bureau

Part des communes avec plusieurs lignes :
- `2014_muni_t1` : `17,61 %`
- `2014_muni_t2` : `25,12 %`
- `2020_muni_t1` : `19,47 %`
- `2020_muni_t2` : `29,00 %`
- `2026_muni_t1` : `19,59 %`
- `2026_muni_t2` : `78,68 %`

Conséquence méthodologique :
- une analyse nationale est faisable.
- une analyse communale est faisable en agrégeant les lignes bureau par `code_commune`.
- une analyse bureau de vote est faisable pour les communes multi-bureaux.
- pour le second tour, la comparabilité temporelle est faible car l'univers des communes concernées change fortement.

Pour agréger au niveau commune :
- grouper par `id_election`, `code_departement`, `code_commune`
- sommer `inscrits`, `abstentions`, `votants`, `blancs`, `nuls`, `exprimes`
- recalculer les ratios après agrégation

## 6. Premières tendances observées

### Synthèse nationale

Premier tour :
- `2014_muni_t1` : participation `63,55 %`, abstention `36,45 %`, nuls/votants `5,49 %`
- `2020_muni_t1` : participation `44,66 %`, abstention `55,34 %`, blancs/votants `1,57 %`, nuls/votants `2,73 %`
- `2026_muni_t1` : participation `57,12 %`, abstention `42,88 %`, blancs/votants `2,65 %`, nuls/votants `2,74 %`

Second tour :
- `2014_muni_t2` : participation `62,13 %`, abstention `37,87 %`, nuls/votants `3,57 %`
- `2020_muni_t2` : participation `41,86 %`, abstention `58,14 %`, blancs/votants `1,67 %`, nuls/votants `1,41 %`
- `2026_muni_t2` : participation `57,09 %`, abstention `42,91 %`, blancs/votants `1,45 %`, nuls/votants `0,98 %`

### Lecture prudente des tendances

- 2020 marque une chute très nette de la participation par rapport à 2014.
- 2026 remonte nettement par rapport à 2020.
- 2026 reste néanmoins en dessous de 2014 au premier tour.
- La part des votes nuls baisse entre 2014 et 2020, puis reste proche en 2026.
- Les votes blancs ne sont comparables qu'entre 2020 et 2026, pas avec 2014.

### Comparaison sur les communes présentes aux trois premiers tours

Communes comparables :
- `34 703` communes sont présentes en `2014_muni_t1`, `2020_muni_t1` et `2026_muni_t1`

Évolution moyenne de la participation sur cet ensemble commun :
- 2014 vers 2020 : `-15,36` points
- 2020 vers 2026 : `+4,97` points
- 2014 vers 2026 : `-10,38` points

Indicateurs complémentaires :
- `66,42 %` des communes comparables ont une participation 2026 supérieure à 2020
- `83,66 %` des communes comparables ont une participation 2026 inférieure à 2014

Second tour :
- seulement `392` communes sont présentes dans les trois millésimes
- le second tour est donc peu adapté à une comparaison temporelle générale

## 7. Limites du dataset

Ce qu'on peut faire avec ce dataset seul :
- analyser la participation et l'abstention
- comparer blancs et nuls entre 2020 et 2026
- cartographier des écarts territoriaux de participation
- comparer des dynamiques de premier tour entre communes
- descendre au bureau de vote dans les communes multi-bureaux

Ce qu'on ne peut pas faire avec ce dataset seul :
- expliquer socio-économiquement les comportements électoraux
- étudier les effets du revenu, de l'âge, du diplôme, de l'emploi, de l'urbanité
- mesurer des votes de partis, de listes ou de blocs politiques
- analyser les déterminants des résultats électoraux au sens partisan
- inférer des causalités

Conclusion claire :
- pour une problématique socio-économique, ce dataset seul ne suffit pas.
- Il faut obligatoirement le croiser avec des données externes, par exemple INSEE.

## 8. Problématiques possibles

### Problématique 1
Comment la participation municipale a-t-elle évolué entre 2014, 2020 et 2026 à l'échelle communale en France ?

Intérêt :
- faisable avec le dataset seul
- robuste car fondé sur des variables bien disponibles
- comparabilité correcte au premier tour

### Problématique 2
Dans quelles communes la baisse de participation entre 2014 et 2020 a-t-elle été la plus forte, et la remontée de 2026 a-t-elle compensé ce recul ?

Intérêt :
- faisable avec le dataset seul
- très bien adapté à une analyse longitudinale sur les communes communes aux trois années

### Problématique 3
Dans les communes multi-bureaux, observe-t-on une hétérogénéité intra-communale durable de la participation entre 2014, 2020 et 2026 ?

Intérêt :
- original
- exploite le niveau bureau de vote
- suppose toutefois de se concentrer sur un sous-ensemble de communes disposant de plusieurs bureaux

## 9. Hypothèses cohérentes avec les données

- H1. La participation au premier tour est nettement plus faible en 2020 qu'en 2014 dans la majorité des communes.
- H2. La participation au premier tour remonte en 2026 par rapport à 2020, sans retrouver le niveau de 2014 dans la majorité des communes.
- H3. Les écarts de participation entre communes restent élevés sur les trois années.
- H4. Les votes blancs parmi les votants sont plus élevés en 2026 qu'en 2020 au premier tour.
- H5. Dans les communes multi-bureaux, les écarts de participation entre bureaux d'une même commune sont suffisamment marqués pour justifier une analyse infra-communale.

## 10. Recommandation finale

Meilleure problématique recommandée :

**Comment la participation municipale a-t-elle évolué entre 2014, 2020 et 2026 à l'échelle communale en France, et dans quelle mesure la remontée observée en 2026 compense-t-elle la rupture de 2020 ?**

Pourquoi c'est la meilleure option :
- elle repose sur les variables les plus fiables du fichier
- elle évite de dépendre des votes blancs de 2014, absents
- elle n'exige pas de données externes pour une première version solide
- elle permet une analyse nationale, départementale et communale
- elle reste compatible avec un enrichissement socio-économique ultérieur si tu veux aller plus loin

## Fichiers produits

- Script notebook-friendly : `eda_municipales_2014_2020_2026.py`
- Sorties tabulaires : dossier `outputs/`
- Figures : `outputs/figures/`
