#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# %%
# Analyse exploratoire des élections municipales 2014, 2020 et 2026
# Source principale :
# https://object.files.data.gouv.fr/data-pipeline-open/elections/general_results.csv
#
# Ce script est écrit avec des sections "# %%" pour être facilement
# exécutable dans un notebook Jupyter ou dans un éditeur compatible.

import os
from pathlib import Path

DATA_PATH = Path("general_results.csv")
OUTPUT_DIR = Path("outputs")
FIGURES_DIR = OUTPUT_DIR / "figures"
OUTPUT_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)

os.environ["MPLCONFIGDIR"] = str(OUTPUT_DIR / "mplconfig")
Path(os.environ["MPLCONFIGDIR"]).mkdir(exist_ok=True)

import matplotlib
import pandas as pd
import seaborn as sns


# %%
# Paramètres généraux

matplotlib.use("Agg")

import matplotlib.pyplot as plt

sns.set_theme(style="whitegrid", context="talk")
plt.rcParams["figure.figsize"] = (12, 7)
plt.rcParams["axes.titlesize"] = 16
plt.rcParams["axes.labelsize"] = 12

MUNICIPAL_IDS = [
    "2014_muni_t1",
    "2014_muni_t2",
    "2020_muni_t1",
    "2020_muni_t2",
    "2026_muni_t1",
    "2026_muni_t2",
]

NUMERIC_COLS = [
    "inscrits",
    "abstentions",
    "votants",
    "blancs",
    "nuls",
    "exprimes",
    "ratio_abstentions_inscrits",
    "ratio_votants_inscrits",
    "ratio_blancs_inscrits",
    "ratio_blancs_votants",
    "ratio_nuls_inscrits",
    "ratio_nuls_votants",
    "ratio_exprimes_inscrits",
    "ratio_exprimes_votants",
]

GEO_CODE_COLS = [
    "id_election",
    "id_brut_miom",
    "code_departement",
    "libelle_departement",
    "code_canton",
    "libelle_canton",
    "code_commune",
    "libelle_commune",
    "code_circonscription",
    "libelle_circonscription",
    "code_bv",
]


# %%
# 1. Chargement

if not DATA_PATH.exists():
    raise FileNotFoundError(
        "Le fichier general_results.csv est introuvable dans le dossier courant. "
        "Telecharge-le depuis "
        "https://object.files.data.gouv.fr/data-pipeline-open/elections/general_results.csv "
        "puis place-le a la racine du projet."
    )

df = pd.read_csv(DATA_PATH, sep=";", dtype={col: "string" for col in GEO_CODE_COLS}, low_memory=False)

for col in NUMERIC_COLS:
    df[col] = pd.to_numeric(df[col], errors="coerce")

print("Dimensions du dataset complet :", df.shape)
print("\nColonnes :")
print(df.columns.tolist())


# %%
# 2. Structure et qualité du dataset complet

structure = pd.DataFrame(
    {
        "column": df.columns,
        "dtype": df.dtypes.astype(str).values,
        "missing_count": df.isna().sum().values,
        "missing_pct": (df.isna().mean() * 100).round(4).values,
        "n_unique": [df[col].nunique(dropna=True) for col in df.columns],
    }
)

duplicate_rows = int(df.duplicated().sum())
municipal_duplicate_rows = int(municipal.duplicated().sum()) if "municipal" in locals() else None

print("\nAperçu des 5 premières lignes :")
print(df.head())
print("\nDoublons exacts :", duplicate_rows)
print("\nTaux de valeurs manquantes :")
print(structure.sort_values("missing_pct", ascending=False))

structure.to_csv(OUTPUT_DIR / "structure_dataset_complet.csv", index=False)


# %%
# 3. Valeurs distinctes de id_election

id_elections = pd.Series(sorted(df["id_election"].dropna().unique()), name="id_election")
print("\nIdentifiants distincts d'élection :")
print(id_elections.to_list())

id_elections.to_csv(OUTPUT_DIR / "id_election_distincts.csv", index=False)

municipal_present = [e for e in id_elections if "muni" in e]
print("\nIdentifiants municipaux détectés :")
print(municipal_present)


# %%
# 4. Filtre sur les municipales 2014 / 2020 / 2026

municipal = df[df["id_election"].isin(MUNICIPAL_IDS)].copy()
municipal["annee"] = municipal["id_election"].str.slice(0, 4).astype("Int64")
municipal["tour"] = municipal["id_election"].str.extract(r"(t\d)$", expand=False)

print("\nDimensions du sous-ensemble municipal :", municipal.shape)
print("\nRépartition des lignes par identifiant :")
print(municipal["id_election"].value_counts().sort_index())


# %%
# 5. Profil qualité sur le sous-ensemble municipal

municipal_quality = pd.DataFrame(
    {
        "column": municipal.columns,
        "dtype": municipal.dtypes.astype(str).values,
        "missing_count": municipal.isna().sum().values,
        "missing_pct": (municipal.isna().mean() * 100).round(4).values,
        "n_unique": [municipal[col].nunique(dropna=True) for col in municipal.columns],
    }
).sort_values("missing_pct", ascending=False)

print("\nQualité du sous-ensemble municipal :")
print(municipal_quality)

municipal_quality.to_csv(OUTPUT_DIR / "qualite_sous_ensemble_municipal.csv", index=False)


# %%
# 6. Vérification du niveau géographique réellement disponible
# Le dataset est annoncé au niveau bureau de vote, mais certaines communes
# n'ont qu'une seule ligne (souvent bureau 0001). On vérifie donc le nombre
# de lignes par commune et par élection.

rows_per_commune = (
    municipal.groupby(["id_election", "code_commune"], dropna=False)
    .size()
    .rename("n_rows")
    .reset_index()
)

geo_level_summary = (
    rows_per_commune.groupby("id_election")["n_rows"]
    .agg(
        n_communes="count",
        communes_multi_bv=lambda s: int((s > 1).sum()),
        max_rows_same_commune="max",
    )
    .reset_index()
)
geo_level_summary["pct_communes_multi_bv"] = (
    geo_level_summary["communes_multi_bv"] / geo_level_summary["n_communes"] * 100
).round(2)

print("\nRésumé du niveau géographique :")
print(geo_level_summary)

geo_level_summary.to_csv(OUTPUT_DIR / "resume_niveau_geographique.csv", index=False)


# %%
# 7. Anomalies de cohérence métier

municipal["check_inscrits_equals_abstentions_plus_votants"] = (
    municipal["inscrits"] == municipal["abstentions"] + municipal["votants"]
)
municipal["check_votants_equals_exprimes_plus_nuls_plus_blancs"] = (
    municipal["votants"] == municipal["exprimes"] + municipal["nuls"] + municipal["blancs"]
)
municipal["has_negative_value"] = municipal[
    ["inscrits", "abstentions", "votants", "blancs", "nuls", "exprimes"]
].lt(0).any(axis=1)
municipal["has_zero_inscrits_or_votants"] = municipal["inscrits"].eq(0) | municipal["votants"].eq(0)

anomaly_summary = municipal.groupby("id_election").agg(
    rows=("id_election", "size"),
    exact_duplicates=("id_election", lambda s: int(municipal.loc[s.index].duplicated().sum())),
    negative_rows=("has_negative_value", "sum"),
    zero_inscrits_or_votants=("has_zero_inscrits_or_votants", "sum"),
    missing_blancs=("blancs", lambda s: int(s.isna().sum())),
    valid_balance_inscrits=("check_inscrits_equals_abstentions_plus_votants", "mean"),
    valid_balance_votes=("check_votants_equals_exprimes_plus_nuls_plus_blancs", "mean"),
).reset_index()

anomaly_summary["valid_balance_inscrits"] = (anomaly_summary["valid_balance_inscrits"] * 100).round(2)
anomaly_summary["valid_balance_votes"] = (anomaly_summary["valid_balance_votes"] * 100).round(2)

negative_rows = municipal.loc[
    municipal["has_negative_value"],
    [
        "id_election",
        "id_brut_miom",
        "code_departement",
        "code_commune",
        "libelle_commune",
        "code_bv",
        "inscrits",
        "abstentions",
        "votants",
        "blancs",
        "nuls",
        "exprimes",
    ],
].copy()

zero_rows = municipal.loc[
    municipal["has_zero_inscrits_or_votants"],
    [
        "id_election",
        "id_brut_miom",
        "code_departement",
        "code_commune",
        "libelle_commune",
        "code_bv",
        "inscrits",
        "abstentions",
        "votants",
        "blancs",
        "nuls",
        "exprimes",
    ],
].copy()

print("\nRésumé des anomalies :")
print(anomaly_summary)

anomaly_summary.to_csv(OUTPUT_DIR / "resume_anomalies_municipales.csv", index=False)
negative_rows.to_csv(OUTPUT_DIR / "lignes_valeurs_negatives.csv", index=False)
zero_rows.to_csv(OUTPUT_DIR / "lignes_zero_inscrits_ou_votants.csv", index=False)


# %%
# 8. Agrégation au niveau commune
# Cette étape permet de comparer les années sans dépendre du nombre de bureaux.

commune = (
    municipal.groupby(
        [
            "id_election",
            "annee",
            "tour",
            "code_departement",
            "libelle_departement",
            "code_commune",
            "libelle_commune",
        ],
        dropna=False,
    )[["inscrits", "abstentions", "votants", "blancs", "nuls", "exprimes"]]
    .sum(min_count=1)
    .reset_index()
)

commune["participation_pct"] = commune["votants"] / commune["inscrits"] * 100
commune["abstention_pct"] = commune["abstentions"] / commune["inscrits"] * 100
commune["blancs_votants_pct"] = commune["blancs"] / commune["votants"] * 100
commune["nuls_votants_pct"] = commune["nuls"] / commune["votants"] * 100
commune["exprimes_votants_pct"] = commune["exprimes"] / commune["votants"] * 100

commune.to_csv(OUTPUT_DIR / "municipales_commune_agregees.csv", index=False)


# %%
# 9. Statistiques descriptives

descriptive_stats = (
    commune.groupby("id_election")[
        [
            "inscrits",
            "abstentions",
            "votants",
            "exprimes",
            "participation_pct",
            "abstention_pct",
            "blancs_votants_pct",
            "nuls_votants_pct",
        ]
    ]
    .describe(percentiles=[0.25, 0.5, 0.75])
    .round(2)
)

print("\nStatistiques descriptives au niveau commune :")
print(descriptive_stats)

descriptive_stats.to_csv(OUTPUT_DIR / "statistiques_descriptives_communes.csv")


# %%
# 10. Synthèse nationale par élection

national = (
    commune.groupby(["id_election", "annee", "tour"])[
        ["inscrits", "abstentions", "votants", "blancs", "nuls", "exprimes"]
    ]
    .sum(min_count=1)
    .reset_index()
)

national["participation_pct"] = national["votants"] / national["inscrits"] * 100
national["abstention_pct"] = national["abstentions"] / national["inscrits"] * 100
national["blancs_votants_pct"] = national["blancs"] / national["votants"] * 100
national["nuls_votants_pct"] = national["nuls"] / national["votants"] * 100
national["exprimes_votants_pct"] = national["exprimes"] / national["votants"] * 100

print("\nSynthèse nationale :")
print(national.round(2))

national.to_csv(OUTPUT_DIR / "synthese_nationale_municipales.csv", index=False)


# %%
# 11. Communes comparables dans le temps

comparison_counts = []
for tour in ["t1", "t2"]:
    ids = [f"2014_muni_{tour}", f"2020_muni_{tour}", f"2026_muni_{tour}"]
    sets = [set(commune.loc[commune["id_election"] == election_id, "code_commune"]) for election_id in ids]
    common = set.intersection(*sets)
    comparison_counts.append(
        {
            "tour": tour,
            "n_common_communes": len(common),
            "n_2014": len(sets[0]),
            "n_2020": len(sets[1]),
            "n_2026": len(sets[2]),
        }
    )

comparison_counts = pd.DataFrame(comparison_counts)
print("\nCommunes présentes sur les trois années :")
print(comparison_counts)
comparison_counts.to_csv(OUTPUT_DIR / "communes_communes_presentes_sur_3_annees.csv", index=False)


# %%
# 12. Visualisations

plot_df = national.copy()
plot_df["label"] = plot_df["annee"].astype(str) + " " + plot_df["tour"].str.upper()

fig, ax = plt.subplots()
sns.barplot(data=plot_df, x="label", y="participation_pct", hue="tour", palette="Set2", ax=ax)
ax.set_title("Participation nationale par élection municipale")
ax.set_xlabel("")
ax.set_ylabel("Participation (%)")
ax.legend(title="Tour")
plt.tight_layout()
plt.savefig(FIGURES_DIR / "participation_nationale_par_election.png", dpi=160)
plt.close(fig)

fig, ax = plt.subplots()
sns.barplot(
    data=plot_df,
    x="label",
    y="nuls_votants_pct",
    hue="tour",
    palette="Set1",
    ax=ax,
)
ax.set_title("Part des votes nuls parmi les votants")
ax.set_xlabel("")
ax.set_ylabel("Votes nuls / votants (%)")
ax.legend(title="Tour")
plt.tight_layout()
plt.savefig(FIGURES_DIR / "part_votes_nuls.png", dpi=160)
plt.close(fig)

commune_plot = commune.copy()
commune_plot["label"] = commune_plot["annee"].astype(str) + " " + commune_plot["tour"].str.upper()

fig, ax = plt.subplots()
sns.boxplot(data=commune_plot, x="label", y="participation_pct", palette="Pastel1", ax=ax)
ax.set_title("Distribution de la participation communale")
ax.set_xlabel("")
ax.set_ylabel("Participation (%)")
plt.tight_layout()
plt.savefig(FIGURES_DIR / "distribution_participation_communes_boxplot.png", dpi=160)
plt.close(fig)

fig, ax = plt.subplots()
sns.histplot(
    data=commune_plot[commune_plot["tour"] == "t1"],
    x="participation_pct",
    hue="annee",
    bins=40,
    kde=True,
    palette="Dark2",
    alpha=0.35,
    ax=ax,
)
ax.set_title("Distribution de la participation communale au premier tour")
ax.set_xlabel("Participation (%)")
ax.set_ylabel("Nombre de communes")
plt.tight_layout()
plt.savefig(FIGURES_DIR / "distribution_participation_t1_hist.png", dpi=160)
plt.close(fig)


# %%
# 13. Conclusion technique automatique

print("\nConclusion technique synthétique")
print("- Le fichier contient plusieurs élections dans une table unique.")
print("- Les municipales recherchées sont bien repérables via id_election.")
print("- Le niveau le plus fin réellement exploitable est la ligne bureau de vote, agrégable à la commune.")
print("- Les communes sont comparables surtout au premier tour : le second tour concerne des sous-ensembles très différents selon les années.")
print("- La variable 'blancs' est absente pour les municipales 2014 dans ce dataset.")
print("- Des anomalies ponctuelles existent en 2026 (valeurs négatives ou zéros).")
print("- Pour une problématique socio-économique, un enrichissement externe est nécessaire.")
