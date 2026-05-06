# MsprData

Analyse exploratoire des elections municipales 2014, 2020 et 2026, avec une base de travail pour preparer une prediction de la participation aux municipales 2032.

. Clarifier la décision à améliorer
Vous l’avez fait : adapter les campagnes de communication en fonction des niveaux de participation attendus.

2. Reformuler en question analytique
Vous l’avez fait : prédire le taux de participation 2032 en corrigeant l’effet Covid de 2020.

3. Identifier la variable cible
Vous l’avez fait : taux_participation = Votants / Inscrits × 100.

4. Vérifier la faisabilité (métier, technique, données, qualité, représentativité)
Vous avez rempli la grille et obtenu un score de 14/16.



1. Clarifier la décision à améliorer
Vous l’avez fait : adapter les campagnes de communication en fonction des niveaux de participation attendus.

2. Reformuler en question analytique
Vous l’avez fait : prédire le taux de participation 2032 en corrigeant l’effet Covid de 2020.

3. Identifier la variable cible
Vous l’avez fait : taux_participation = Votants / Inscrits × 100.

4. Vérifier la faisabilité (métier, technique, données, qualité, représentativité)
Vous avez rempli la grille et obtenu un score de 14/16.
5. Définir les critères de succès
Vous avez fixé une MAE < 2,5 points, un intervalle de confiance



# sCharger et inspecter vos fichiers de données



Passer à l’action concrète (étape suivante)
Une fois le cadrage validé, la première étape technique est :

Charger et inspecter vos fichiers de données
elections_2014.csv, elections_2020.csv, elections_2026.csv



# cCharger et inspecter vos fichiers de données



population.csv, chomage.csv, revenus_pauvrete.csv, crimes_delits.csv

Comme dans le notebook fil rouge (vélos), vous devez :

Lire chaque fichier avec pandas

Normaliser les noms de colonnes (ex: Code de la commune → code_insee, Inscrits → inscrits)

Vérifier les types, les valeurs manquantes, les doublons

Construire la variable taux_participation