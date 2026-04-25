"""Fonctions de chargement et d'inspection des jeux de donnees.

Ce module se concentre sur deux besoins :
1. charger des CSV heterogenes sans supposer un encodage ou un separateur unique ;
2. produire un diagnostic rapide avant nettoyage et fusion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Tuple
import re
import unicodedata

import numpy as np
import pandas as pd


EXPECTED_FILES = {
    "elections_2014": "elections_2014.csv",
    "elections_2020": "elections_2020.csv",
    "elections_2026": "elections_2026.csv",
    "population": "population.csv",
    "chomage": "chomage.csv",
    "revenus_pauvrete": "revenus_pauvrete.csv",
    "crimes_delits": "crimes_delits.csv",
}


def normalize_text(value: object) -> str:
    """Normalise un texte pour faciliter la detection de colonnes."""

    if value is None:
        return ""

    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def make_unique_names(columns: Iterable[object]) -> List[str]:
    """Transforme des noms de colonnes en snake_case et les rend uniques."""

    unique_names: List[str] = []
    counters: Dict[str, int] = {}

    for column in columns:
        base_name = normalize_text(column) or "colonne"
        current_count = counters.get(base_name, 0)

        if current_count == 0:
            candidate = base_name
        else:
            candidate = f"{base_name}_{current_count + 1}"

        counters[base_name] = current_count + 1
        unique_names.append(candidate)

    return unique_names


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les noms de colonnes et supprime les colonnes vides."""

    cleaned_df = df.copy()
    cleaned_df.columns = make_unique_names(cleaned_df.columns)

    unnamed_columns = [
        column
        for column in cleaned_df.columns
        if column.startswith("unnamed") and cleaned_df[column].isna().all()
    ]
    if unnamed_columns:
        cleaned_df = cleaned_df.drop(columns=unnamed_columns)

    return cleaned_df


def load_csv_flexible(file_path: Path | str) -> pd.DataFrame:
    """Charge un CSV en essayant plusieurs encodages et separateurs.

    Cette fonction est volontairement defensive car les exports publics
    changent souvent d'encodage, de separateur et de convention d'en-tete.
    """

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    encodings = ("utf-8", "utf-8-sig", "latin-1", "cp1252")
    separators = (None, ";", ",", "\t", "|")
    last_error: Exception | None = None
    fallback_df: pd.DataFrame | None = None

    for encoding in encodings:
        for separator in separators:
            try:
                read_kwargs = {
                    "filepath_or_buffer": path,
                    "encoding": encoding,
                    "low_memory": False,
                }

                if separator is None:
                    read_kwargs["sep"] = None
                    read_kwargs["engine"] = "python"
                else:
                    read_kwargs["sep"] = separator

                df = pd.read_csv(**read_kwargs)
                df = clean_column_names(df)

                if df.shape[1] > 1:
                    return df

                if fallback_df is None:
                    fallback_df = df
            except Exception as error:  # pragma: no cover - defense utile en vrai.
                last_error = error

    if fallback_df is not None:
        return fallback_df

    raise ValueError(
        f"Echec du chargement du fichier {path}. Derniere erreur : {last_error}"
    )


def load_expected_datasets(
    data_dir: Path | str = "data",
    expected_files: Dict[str, str] | None = None,
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, Path]]:
    """Charge tous les jeux de donnees attendus s'ils existent."""

    base_dir = Path(data_dir)
    file_mapping = expected_files or EXPECTED_FILES

    datasets: Dict[str, pd.DataFrame] = {}
    missing_files: Dict[str, Path] = {}

    for dataset_name, file_name in file_mapping.items():
        file_path = base_dir / file_name
        if file_path.exists():
            datasets[dataset_name] = load_csv_flexible(file_path)
        else:
            missing_files[dataset_name] = file_path

    return datasets, missing_files


def build_dataset_catalog(
    data_dir: Path | str = "data",
    expected_files: Dict[str, str] | None = None,
) -> pd.DataFrame:
    """Construit un catalogue simple des fichiers attendus et de leur presence."""

    base_dir = Path(data_dir)
    file_mapping = expected_files or EXPECTED_FILES
    rows = []

    for dataset_name, file_name in file_mapping.items():
        file_path = base_dir / file_name
        rows.append(
            {
                "dataset": dataset_name,
                "chemin": str(file_path),
                "present": file_path.exists(),
            }
        )

    return pd.DataFrame(rows)


def identify_join_candidates(df: pd.DataFrame) -> List[str]:
    """Repere les colonnes susceptibles de servir de cles de jointure."""

    keywords = [
        "commune",
        "insee",
        "code",
        "geo",
        "libelle",
        "nom",
        "annee",
        "year",
    ]

    candidates = [
        column
        for column in df.columns
        if any(keyword in normalize_text(column) for keyword in keywords)
    ]
    return candidates


def inspect_dataframe(df: pd.DataFrame, dataset_name: str) -> Dict[str, object]:
    """Retourne un resume compact de la structure d'un DataFrame."""

    missing_values = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    return {
        "dataset": dataset_name,
        "n_lignes": int(df.shape[0]),
        "n_colonnes": int(df.shape[1]),
        "colonnes": list(df.columns),
        "dtypes": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "valeurs_manquantes_totales": missing_values,
        "lignes_dupliquees": duplicate_rows,
        "cles_jointure_candidates": identify_join_candidates(df),
    }


def build_inspection_table(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Assemble un tableau synthetique d'inspection multi-datasets."""

    rows = []
    for dataset_name, df in datasets.items():
        info = inspect_dataframe(df, dataset_name)
        rows.append(
            {
                "dataset": info["dataset"],
                "n_lignes": info["n_lignes"],
                "n_colonnes": info["n_colonnes"],
                "valeurs_manquantes_totales": info["valeurs_manquantes_totales"],
                "lignes_dupliquees": info["lignes_dupliquees"],
                "cles_jointure_candidates": ", ".join(info["cles_jointure_candidates"]),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "dataset",
                "n_lignes",
                "n_colonnes",
                "valeurs_manquantes_totales",
                "lignes_dupliquees",
                "cles_jointure_candidates",
            ]
        )

    return pd.DataFrame(rows).sort_values("dataset").reset_index(drop=True)


def missing_values_table(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne un tableau des colonnes manquantes trie par importance."""

    summary = pd.DataFrame(
        {
            "colonne": df.columns,
            "nb_manquants": df.isna().sum().values,
            "pct_manquants": np.round(df.isna().mean().values * 100, 2),
            "dtype": df.dtypes.astype(str).values,
        }
    )

    summary = summary.sort_values(
        by=["nb_manquants", "colonne"], ascending=[False, True]
    ).reset_index(drop=True)
    return summary
