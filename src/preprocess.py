"""Nettoyage, harmonisation et construction du panel electoral final."""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple
import re
import unicodedata

import numpy as np
import pandas as pd
from scipy.stats import ttest_rel, wilcoxon


COMMON_ID_ALIASES = {
    "code_commune": [
        "code_commune",
        "code_commune_insee",
        "code_insee",
        "code_officiel_geographique",
        "codegeo",
        "code_geo",
        "codgeo",
        "codgeo_2025",
        "com",
        "code_com",
        "codcom",
        "codsubcom",
        "code_de_la_commune",
        "code_commune_ou_arm",
        "code_commune_arm",
        "insee_com",
    ],
    "nom_commune": [
        "nom_commune",
        "nom_de_la_commune",
        "libelle_commune",
        "libelle_de_la_commune",
        "commune",
        "libcom",
        "libsubcom",
        "nom_territoire",
        "nom",
        "libelle",
    ],
    "code_departement": [
        "code_departement",
        "code_du_departement",
        "coddpt",
        "code_dep",
        "coddep",
        "dep",
    ],
    "annee": [
        "annee",
        "year",
        "millesime",
        "annee_scrutin",
        "annee_election",
        "annee_source",
    ],
}


ELECTION_ALIASES = {
    **COMMON_ID_ALIASES,
    "nombre_inscrits": [
        "nombre_inscrits",
        "nb_inscrits",
        "inscrits",
        "ins",
        "i",
        "nbrins",
    ],
    "nombre_abstentions": [
        "nombre_abstentions",
        "nb_abstentions",
        "abstentions",
        "abs",
        "a",
        "nbrabs",
    ],
    "nombre_votants": [
        "nombre_votants",
        "nb_votants",
        "votants",
        "vot",
        "v",
        "nbrvot",
    ],
    "nombre_exprimes": [
        "nombre_exprimes",
        "nb_exprimes",
        "exprimes",
        "suffrages_exprimes",
        "suffrages_exprimes_nuls_exclus",
        "e",
        "nbrexp",
    ],
    "taux_participation": [
        "taux_participation",
        "participation",
        "tx_participation",
        "taux_de_participation",
        "pctvotins",
        "vot_ins",
        "pct_vot_ins",
        "votants_2",
        "votants_inscrits",
    ],
    "taux_abstention": [
        "taux_abstention",
        "abstention",
        "tx_abstention",
        "taux_d_abstention",
        "pctabsins",
        "abs_ins",
        "pct_abs_ins",
        "abstentions_2",
        "abstentions_inscrits",
    ],
}


POPULATION_ALIASES = {
    **COMMON_ID_ALIASES,
    "population_totale": [
        "population_totale",
        "population",
        "pop_tot",
        "population_municipale",
        "pmun",
        "ptot",
        "population_legale",
    ],
}


CHOMAGE_ALIASES = {
    **COMMON_ID_ALIASES,
    "taux_chomage": [
        "taux_chomage",
        "chomage",
        "tx_chomage",
        "taux_de_chomage",
        "part_chomeurs",
    ],
    "nombre_chomeurs": [
        "nombre_chomeurs",
        "nb_chomeurs",
        "chomeurs",
    ],
}


REVENUS_ALIASES = {
    **COMMON_ID_ALIASES,
    "revenu_median": [
        "revenu_median",
        "revenu_disponible_median",
        "niveau_vie_median",
        "mediane_niveau_de_vie",
        "med",
    ],
    "taux_pauvrete": [
        "taux_pauvrete",
        "pauvrete",
        "tx_pauvrete",
        "taux_de_pauvrete",
        "part_pauvres",
    ],
}


CRIMES_ALIASES = {
    **COMMON_ID_ALIASES,
    "nombre_faits": [
        "nombre_faits",
        "nb_faits",
        "faits",
        "nombre_crimes_delits",
        "crimes_delits",
    ],
    "taux_criminalite": [
        "taux_criminalite",
        "taux_pour_mille",
        "tauxpourmille",
        "taux_faits",
        "taux_delinquance",
    ],
}


DATASET_ALIAS_MAPS = {
    "population": POPULATION_ALIASES,
    "chomage": CHOMAGE_ALIASES,
    "revenus_pauvrete": REVENUS_ALIASES,
    "crimes_delits": CRIMES_ALIASES,
}


def normalize_text(value: object) -> str:
    """Normalise un texte en ASCII et snake_case."""

    if value is None:
        return ""

    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^\w]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def make_unique_names(columns: Iterable[object]) -> List[str]:
    """Rend les noms de colonnes uniques apres normalisation."""

    unique_names: List[str] = []
    counters: Dict[str, int] = {}

    for column in columns:
        base_name = normalize_text(column) or "colonne"
        count = counters.get(base_name, 0)
        unique_names.append(base_name if count == 0 else f"{base_name}_{count + 1}")
        counters[base_name] = count + 1

    return unique_names


def sanitize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie les noms de colonnes d'un DataFrame."""

    sanitized_df = df.copy()
    sanitized_df.columns = make_unique_names(sanitized_df.columns)
    return sanitized_df


def detect_best_column(columns: Iterable[str], aliases: Iterable[str]) -> str | None:
    """Trouve la meilleure colonne candidate pour un nom canonique."""

    normalized_columns = [normalize_text(column) for column in columns]
    normalized_aliases = [normalize_text(alias) for alias in aliases]

    scored_candidates: List[Tuple[int, int, str]] = []
    for column in normalized_columns:
        column_tokens = set(column.split("_"))
        for alias in normalized_aliases:
            alias_tokens = set(alias.split("_"))
            if not alias:
                continue
            if column == alias:
                scored_candidates.append((100, len(alias_tokens), column))
            elif alias_tokens and alias_tokens.issubset(column_tokens):
                scored_candidates.append((10, len(alias_tokens), column))
            elif column.startswith(f"{alias}_") or column.endswith(f"_{alias}"):
                scored_candidates.append((5, len(alias_tokens), column))

    if not scored_candidates:
        return None

    scored_candidates.sort(reverse=True)
    return scored_candidates[0][2]


def standardize_columns(
    df: pd.DataFrame, alias_mapping: Dict[str, List[str]]
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Renomme les colonnes detectees vers des noms canoniques."""

    standardized_df = sanitize_dataframe_columns(df)
    rename_map: Dict[str, str] = {}
    available_columns = list(standardized_df.columns)
    canonical_columns = set(alias_mapping.keys())
    used_source_columns = set()

    for canonical_name, aliases in alias_mapping.items():
        if canonical_name in standardized_df.columns:
            continue

        candidate_columns = [
            column
            for column in available_columns
            if column not in used_source_columns and column not in canonical_columns
        ]
        detected_column = detect_best_column(candidate_columns, [canonical_name, *aliases])
        if detected_column and detected_column not in rename_map:
            rename_map[detected_column] = canonical_name
            used_source_columns.add(detected_column)

    standardized_df = standardized_df.rename(columns=rename_map)
    return standardized_df, rename_map


def standardize_department_code(series: pd.Series) -> pd.Series:
    """Uniformise le code departement, y compris certains codes ultramarins historiques."""

    special_mapping = {
        "ZA": "971",
        "ZB": "972",
        "ZC": "973",
        "ZD": "974",
        "ZS": "975",
        "ZM": "976",
        "ZP": "987",
    }

    cleaned = (
        series.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"[^0-9A-Z]", "", regex=True)
    )
    cleaned = cleaned.replace(special_mapping)

    purely_numeric = cleaned.str.fullmatch(r"\d+")
    overseas_mask = purely_numeric & cleaned.str.startswith(("97", "98"))
    cleaned.loc[purely_numeric & ~overseas_mask] = cleaned.loc[
        purely_numeric & ~overseas_mask
    ].str.zfill(2)
    cleaned.loc[overseas_mask] = cleaned.loc[overseas_mask].str.zfill(3)
    cleaned = cleaned.replace({"": np.nan, "NAN": np.nan, "NONE": np.nan})
    return cleaned


def standardize_commune_code(series: pd.Series) -> pd.Series:
    """Uniformise le code commune en chaine stable pour les jointures."""

    cleaned = (
        series.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"[^0-9A-Z]", "", regex=True)
    )

    purely_numeric = cleaned.str.fullmatch(r"\d+")
    cleaned.loc[purely_numeric] = cleaned.loc[purely_numeric].str.zfill(5)
    cleaned = cleaned.replace({"": np.nan, "NAN": np.nan, "NONE": np.nan})
    return cleaned


def reconstruct_commune_code(
    code_commune: pd.Series, code_departement: pd.Series | None = None
) -> pd.Series:
    """Reconstruit un code commune complet quand seule la partie communale est disponible."""

    cleaned_code = (
        code_commune.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"[^0-9A-Z]", "", regex=True)
    )
    cleaned_code = cleaned_code.replace({"": np.nan, "NAN": np.nan, "NONE": np.nan})

    if code_departement is None:
        return standardize_commune_code(cleaned_code)

    cleaned_department = standardize_department_code(code_departement)
    pure_numeric_code = cleaned_code.str.fullmatch(r"\d+")
    short_code = cleaned_code.str.len().fillna(0) <= 3
    needs_prefix = cleaned_department.notna() & pure_numeric_code & short_code
    cleaned_code.loc[needs_prefix] = (
        cleaned_department.loc[needs_prefix]
        + cleaned_code.loc[needs_prefix].str.zfill(3)
    )
    return standardize_commune_code(cleaned_code)


def standardize_commune_name(series: pd.Series) -> pd.Series:
    """Nettoie le nom de commune pour un usage descriptif et de secours."""

    cleaned = (
        series.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )
    cleaned = cleaned.replace({"": np.nan, "NAN": np.nan, "NONE": np.nan})
    return cleaned


def parse_numeric_series(series: pd.Series) -> pd.Series:
    """Convertit une serie heterogene en numerique de facon robuste."""

    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    cleaned = series.astype(str).str.strip()
    cleaned = cleaned.replace(
        {
            "": np.nan,
            "nan": np.nan,
            "NaN": np.nan,
            "None": np.nan,
            "ND": np.nan,
            "n.d.": np.nan,
            "s": np.nan,
        }
    )
    cleaned = cleaned.str.replace("\xa0", "", regex=False)
    cleaned = cleaned.str.replace(" ", "", regex=False)
    cleaned = cleaned.str.replace("%", "", regex=False)

    both_separators = cleaned.str.contains(",", na=False) & cleaned.str.contains(".", na=False)
    cleaned.loc[both_separators] = cleaned.loc[both_separators].str.replace(".", "", regex=False)
    cleaned = cleaned.str.replace(",", ".", regex=False)
    cleaned = cleaned.str.replace(r"[^0-9\.\-]", "", regex=True)

    return pd.to_numeric(cleaned, errors="coerce")


def infer_department_code(series: pd.Series) -> pd.Series:
    """Derive un code departement a partir du code commune."""

    def _department_from_code(value: object) -> object:
        if pd.isna(value):
            return np.nan

        code = str(value).upper()
        if len(code) < 2:
            return np.nan

        if code.startswith(("97", "98")) and len(code) >= 3:
            return code[:3]

        return code[:2]

    return series.apply(_department_from_code)


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divise deux series en gerant les zeros."""

    denominator = denominator.replace(0, np.nan)
    return numerator / denominator


def collapse_duplicate_rows(
    df: pd.DataFrame, group_columns: List[str], sum_columns: Iterable[str] | None = None
) -> pd.DataFrame:
    """Agrege les doublons en preservant les cles principales."""

    if not group_columns:
        return df.drop_duplicates().reset_index(drop=True)

    working_df = df.copy()
    sum_columns = set(sum_columns or [])
    numeric_columns = [
        column
        for column in working_df.select_dtypes(include=[np.number]).columns
        if column not in group_columns
    ]
    object_columns = [
        column
        for column in working_df.columns
        if column not in group_columns and column not in numeric_columns
    ]

    aggregation = {}
    for column in numeric_columns:
        aggregation[column] = "sum" if column in sum_columns else "mean"

    def first_non_null(values: pd.Series) -> object:
        non_null = values.dropna()
        if non_null.empty:
            return np.nan
        return non_null.iloc[0]

    for column in object_columns:
        aggregation[column] = first_non_null

    collapsed = (
        working_df.groupby(group_columns, dropna=False, as_index=False)
        .agg(aggregation)
        .reset_index(drop=True)
    )
    return collapsed


def auto_cast_numeric_columns(
    df: pd.DataFrame, protected_columns: Iterable[str] | None = None
) -> pd.DataFrame:
    """Convertit automatiquement les colonnes textuelles numeriques."""

    protected = set(protected_columns or [])
    converted_df = df.copy()

    for column in converted_df.columns:
        if column in protected:
            continue

        if pd.api.types.is_numeric_dtype(converted_df[column]):
            continue

        converted = parse_numeric_series(converted_df[column])
        original_non_null = converted_df[column].notna().sum()
        converted_non_null = converted.notna().sum()

        if original_non_null == 0:
            continue

        if converted_non_null >= max(3, int(original_non_null * 0.5)):
            converted_df[column] = converted

    return converted_df


def preprocess_election_dataframe(
    df: pd.DataFrame, year: int
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Prepare un jeu electoral communal a l'echelle voulue."""

    working_df, rename_map = standardize_columns(df, ELECTION_ALIASES)

    if "code_departement" in working_df.columns:
        working_df["code_departement"] = standardize_department_code(
            working_df["code_departement"]
        )

    if "annee" not in working_df.columns:
        working_df["annee"] = year
    else:
        working_df["annee"] = parse_numeric_series(working_df["annee"]).fillna(year)

    if "code_commune" in working_df.columns:
        working_df["code_commune"] = reconstruct_commune_code(
            working_df["code_commune"],
            working_df["code_departement"] if "code_departement" in working_df.columns else None,
        )
    if "nom_commune" in working_df.columns:
        working_df["nom_commune"] = standardize_commune_name(working_df["nom_commune"])

    working_df["annee"] = parse_numeric_series(working_df["annee"]).fillna(year).astype(int)
    working_df["covid_2020"] = (working_df["annee"] == 2020).astype(int)

    quantitative_columns = [
        "nombre_inscrits",
        "nombre_abstentions",
        "nombre_votants",
        "nombre_exprimes",
        "taux_participation",
        "taux_abstention",
    ]
    for column in quantitative_columns:
        if column in working_df.columns:
            working_df[column] = parse_numeric_series(working_df[column])

    for rate_column in ["taux_participation", "taux_abstention"]:
        if rate_column in working_df.columns:
            invalid_values = ~working_df[rate_column].between(0, 100, inclusive="both")
            working_df.loc[invalid_values, rate_column] = np.nan

    if "nombre_votants" not in working_df.columns and {
        "nombre_inscrits",
        "nombre_abstentions",
    }.issubset(working_df.columns):
        working_df["nombre_votants"] = (
            working_df["nombre_inscrits"] - working_df["nombre_abstentions"]
        )

    if "nombre_abstentions" not in working_df.columns and {
        "nombre_inscrits",
        "nombre_votants",
    }.issubset(working_df.columns):
        working_df["nombre_abstentions"] = (
            working_df["nombre_inscrits"] - working_df["nombre_votants"]
        )

    if {"nombre_votants", "nombre_inscrits"}.issubset(working_df.columns):
        participation_calc = np.round(
            safe_divide(working_df["nombre_votants"], working_df["nombre_inscrits"]) * 100,
            2,
        )
        if "taux_participation" not in working_df.columns:
            working_df["taux_participation"] = participation_calc
        else:
            missing_mask = working_df["taux_participation"].isna()
            working_df.loc[missing_mask, "taux_participation"] = participation_calc.loc[missing_mask]

    if {"nombre_abstentions", "nombre_inscrits"}.issubset(working_df.columns):
        abstention_calc = np.round(
            safe_divide(working_df["nombre_abstentions"], working_df["nombre_inscrits"]) * 100,
            2,
        )
        if "taux_abstention" not in working_df.columns:
            working_df["taux_abstention"] = abstention_calc
        else:
            missing_mask = working_df["taux_abstention"].isna()
            working_df.loc[missing_mask, "taux_abstention"] = abstention_calc.loc[missing_mask]

    if "taux_abstention" not in working_df.columns and "taux_participation" in working_df.columns:
        working_df["taux_abstention"] = np.round(100 - working_df["taux_participation"], 2)

    if "taux_participation" not in working_df.columns and "taux_abstention" in working_df.columns:
        working_df["taux_participation"] = np.round(100 - working_df["taux_abstention"], 2)

    essential_columns = [
        "code_commune",
        "nom_commune",
        "annee",
        "covid_2020",
        "nombre_inscrits",
        "nombre_abstentions",
        "nombre_votants",
        "nombre_exprimes",
        "taux_participation",
        "taux_abstention",
    ]
    available_columns = [column for column in essential_columns if column in working_df.columns]
    working_df = working_df[available_columns].copy()

    if "code_commune" in working_df.columns:
        working_df["code_departement"] = infer_department_code(working_df["code_commune"])

    commune_keys = [
        column for column in ["code_commune", "nom_commune"] if column in working_df.columns
    ]
    dedup_keys = commune_keys + (["annee"] if "annee" in working_df.columns and commune_keys else [])
    duplicate_count = int(working_df.duplicated(subset=dedup_keys).sum()) if dedup_keys else int(working_df.duplicated().sum())
    working_df = collapse_duplicate_rows(working_df, dedup_keys)

    metadata = {
        "year": year,
        "rename_map": rename_map,
        "duplicate_rows_before_aggregation": duplicate_count,
        "n_rows_after_preprocess": int(len(working_df)),
    }
    return working_df, metadata


def preprocess_contextual_dataframe(
    df: pd.DataFrame, dataset_name: str
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Prepare un dataset contextuel avant fusion."""

    alias_map = DATASET_ALIAS_MAPS.get(dataset_name, COMMON_ID_ALIASES)
    working_df, rename_map = standardize_columns(df, alias_map)

    if "code_departement" in working_df.columns:
        working_df["code_departement"] = standardize_department_code(
            working_df["code_departement"]
        )
    if "code_commune" in working_df.columns:
        working_df["code_commune"] = reconstruct_commune_code(
            working_df["code_commune"],
            working_df["code_departement"] if "code_departement" in working_df.columns else None,
        )
    if "nom_commune" in working_df.columns:
        working_df["nom_commune"] = standardize_commune_name(working_df["nom_commune"])
    if "annee" in working_df.columns:
        working_df["annee"] = parse_numeric_series(working_df["annee"])

    protected_columns = {"code_commune", "nom_commune", "annee", "code_departement"}
    working_df = auto_cast_numeric_columns(working_df, protected_columns=protected_columns)

    if "code_commune" in working_df.columns and "code_departement" not in working_df.columns:
        working_df["code_departement"] = infer_department_code(working_df["code_commune"])

    commune_group_columns = [
        column for column in ["code_commune", "nom_commune"] if column in working_df.columns
    ]
    group_columns = commune_group_columns + (
        ["annee"] if "annee" in working_df.columns and commune_group_columns else []
    )
    sum_columns = {"nombre_faits"} if dataset_name == "crimes_delits" else set()
    if group_columns:
        duplicate_count = int(working_df.duplicated(subset=group_columns).sum())
        working_df = collapse_duplicate_rows(working_df, group_columns, sum_columns=sum_columns)
    else:
        duplicate_count = int(working_df.duplicated().sum())
        working_df = working_df.drop_duplicates().reset_index(drop=True)

    metadata = {
        "dataset_name": dataset_name,
        "rename_map": rename_map,
        "duplicate_rows_before_aggregation": duplicate_count,
        "n_rows_after_preprocess": int(len(working_df)),
    }
    return working_df, metadata


def build_election_panel(
    election_datasets: Dict[int, pd.DataFrame]
) -> Tuple[pd.DataFrame, Dict[int, Dict[str, object]]]:
    """Concatene les elections preprocesses en un panel 2014-2020-2026."""

    processed_frames = []
    metadata_by_year: Dict[int, Dict[str, object]] = {}

    for year, df in sorted(election_datasets.items()):
        processed_df, metadata = preprocess_election_dataframe(df, year)
        processed_frames.append(processed_df)
        metadata_by_year[year] = metadata

    if not processed_frames:
        return pd.DataFrame(), metadata_by_year

    panel_df = pd.concat(processed_frames, ignore_index=True, sort=False)
    sort_columns = [column for column in ["code_commune", "nom_commune", "annee"] if column in panel_df.columns]
    if sort_columns:
        panel_df = panel_df.sort_values(sort_columns).reset_index(drop=True)

    return panel_df, metadata_by_year


def merge_contextual_dataset(
    base_df: pd.DataFrame, context_df: pd.DataFrame, dataset_name: str
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Fusionne un dataset contextuel avec le panel electoral."""

    if base_df.empty or context_df.empty:
        return base_df.copy(), {
            "dataset": dataset_name,
            "status": "ignore",
            "motif": "base_vide_ou_dataset_contextuel_vide",
        }

    if "code_commune" in base_df.columns and "code_commune" in context_df.columns:
        join_keys = ["code_commune"]
    elif "nom_commune" in base_df.columns and "nom_commune" in context_df.columns:
        join_keys = ["nom_commune"]
    else:
        return base_df.copy(), {
            "dataset": dataset_name,
            "status": "ignore",
            "motif": "aucune_cle_commune_compatible",
        }

    if (
        "annee" in base_df.columns
        and "annee" in context_df.columns
        and context_df["annee"].notna().any()
    ):
        prepared_context = align_contextual_years(base_df, context_df, join_keys)
        merge_keys = [*join_keys, "annee"]
    else:
        prepared_context = context_df.copy()
        merge_keys = join_keys

    conflict_columns = [
        column
        for column in prepared_context.columns
        if column not in merge_keys and column in base_df.columns
    ]
    rename_conflicts = {column: f"{dataset_name}_{column}" for column in conflict_columns}
    prepared_context = prepared_context.rename(columns=rename_conflicts)

    merge_indicator = f"_merge_{dataset_name}"
    merged_df = base_df.merge(
        prepared_context,
        how="left",
        on=merge_keys,
        indicator=merge_indicator,
    )

    match_counts = merged_df[merge_indicator].value_counts(dropna=False).to_dict()
    merged_df = merged_df.drop(columns=[merge_indicator])

    log = {
        "dataset": dataset_name,
        "status": "fusion_ok",
        "cles_utilisees": merge_keys,
        "lignes_avant": int(len(base_df)),
        "lignes_apres": int(len(merged_df)),
        "jointures_reussies": int(match_counts.get("both", 0)),
        "lignes_sans_match": int(match_counts.get("left_only", 0)),
    }
    return merged_df, log


def align_contextual_years(
    base_df: pd.DataFrame,
    context_df: pd.DataFrame,
    join_keys: List[str],
) -> pd.DataFrame:
    """Aligne les donnees contextuelles sur l'annee electorale la plus pertinente.

    Regle :
    - on privilegie la derniere annee contextuelle disponible inferieure ou egale a l'annee electorale ;
    - s'il n'existe aucune annee passee, on retient l'annee la plus proche.
    """

    base_keys = base_df[join_keys + ["annee"]].drop_duplicates().reset_index(drop=True)
    base_keys["_base_row_id"] = np.arange(len(base_keys))

    prepared_context = context_df.rename(columns={"annee": "annee_source"}).copy()
    aligned = base_keys.merge(prepared_context, how="left", on=join_keys)

    if aligned.empty:
        return base_keys.drop(columns=["_base_row_id"])

    aligned["has_context"] = aligned["annee_source"].notna().astype(int)
    aligned["is_past_or_present"] = (
        aligned["annee_source"].le(aligned["annee"]).fillna(False).astype(int)
    )
    aligned["abs_gap"] = (aligned["annee_source"] - aligned["annee"]).abs()
    aligned["abs_gap"] = aligned["abs_gap"].fillna(np.inf)
    aligned["tie_breaker"] = np.where(
        aligned["is_past_or_present"] == 1,
        -aligned["annee_source"].fillna(-np.inf),
        aligned["annee_source"].fillna(np.inf),
    )

    aligned = aligned.sort_values(
        by=["_base_row_id", "has_context", "is_past_or_present", "abs_gap", "tie_breaker"],
        ascending=[True, False, False, True, True],
    )
    aligned = aligned.drop_duplicates(subset=["_base_row_id"], keep="first")
    aligned = aligned.drop(columns=["_base_row_id", "has_context", "is_past_or_present", "abs_gap", "tie_breaker"])
    return aligned


def build_final_dataset(
    election_panel: pd.DataFrame,
    contextual_datasets: Dict[str, pd.DataFrame],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Construit le dataset final par commune et par annee."""

    final_df = election_panel.copy()
    merge_logs = []

    for dataset_name, context_df in contextual_datasets.items():
        final_df, log = merge_contextual_dataset(final_df, context_df, dataset_name)
        merge_logs.append(log)

    sort_columns = [column for column in ["code_commune", "nom_commune", "annee"] if column in final_df.columns]
    if sort_columns:
        final_df = final_df.sort_values(sort_columns).reset_index(drop=True)

    return final_df, pd.DataFrame(merge_logs)


def summarize_final_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Produit un resume du dataset final."""

    if df.empty:
        return pd.DataFrame(
            [
                {
                    "n_lignes": 0,
                    "n_colonnes": 0,
                    "nb_communes": 0,
                    "annees_disponibles": "",
                    "valeurs_manquantes_totales": 0,
                }
            ]
        )

    nb_communes = (
        df["code_commune"].nunique()
        if "code_commune" in df.columns
        else df["nom_commune"].nunique() if "nom_commune" in df.columns else np.nan
    )
    annees = (
        ", ".join(str(int(year)) for year in sorted(df["annee"].dropna().unique()))
        if "annee" in df.columns
        else ""
    )

    return pd.DataFrame(
        [
            {
                "n_lignes": int(df.shape[0]),
                "n_colonnes": int(df.shape[1]),
                "nb_communes": nb_communes,
                "annees_disponibles": annees,
                "valeurs_manquantes_totales": int(df.isna().sum().sum()),
            }
        ]
    )


def compute_yearly_summary(
    df: pd.DataFrame,
    metrics: Iterable[str] = ("nombre_votants", "taux_participation"),
) -> pd.DataFrame:
    """Resume descriptif par annee pour les variables principales."""

    available_metrics = [metric for metric in metrics if metric in df.columns]
    if not available_metrics or "annee" not in df.columns:
        return pd.DataFrame()

    summary = (
        df.groupby("annee")[available_metrics]
        .agg(["mean", "median", "std", "min", "max", "count"])
        .round(2)
    )
    return summary


def compute_descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne les statistiques descriptives globales des colonnes numeriques."""

    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return pd.DataFrame()

    return numeric_df.describe().T.round(2)


def compute_commune_variation(
    df: pd.DataFrame,
    metric: str,
    year_from: int,
    year_to: int,
) -> pd.DataFrame:
    """Calcule les evolutions communales entre deux annees."""

    required_columns = [metric, "annee"]
    if not all(column in df.columns for column in required_columns):
        return pd.DataFrame()

    index_columns = [
        column
        for column in ["code_commune", "nom_commune"]
        if column in df.columns
    ]
    if not index_columns:
        return pd.DataFrame()

    pivot = df.pivot_table(
        index=index_columns,
        columns="annee",
        values=metric,
        aggfunc="mean",
    )

    if year_from not in pivot.columns or year_to not in pivot.columns:
        return pd.DataFrame()

    variation_df = pivot[[year_from, year_to]].dropna().reset_index()
    variation_df["variation_absolue"] = variation_df[year_to] - variation_df[year_from]
    variation_df["variation_relative_pct"] = np.round(
        safe_divide(
            variation_df["variation_absolue"],
            variation_df[year_from].replace(0, np.nan),
        )
        * 100,
        2,
    )
    variation_df = variation_df.sort_values("variation_absolue").reset_index(drop=True)
    return variation_df


def add_period_label(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute une etiquette interpretable avant / pendant / apres Covid."""

    labeled_df = df.copy()
    if "annee" not in labeled_df.columns:
        return labeled_df

    mapping = {
        2014: "Avant Covid",
        2020: "Pendant Covid",
        2026: "Apres Covid",
    }
    labeled_df["periode_covid"] = labeled_df["annee"].map(mapping).fillna("Autre")
    return labeled_df


def analyze_2020_atypicality(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Produit des indicateurs simples pour montrer l'anomalie de 2020."""

    if "annee" not in df.columns or "taux_participation" not in df.columns:
        return {
            "summary": pd.DataFrame(),
            "relative_gaps": pd.DataFrame(),
            "tests": pd.DataFrame(),
        }

    summary = (
        df.groupby("annee")["taux_participation"]
        .agg(["mean", "median", "std", "count"])
        .round(2)
        .reset_index()
    )

    yearly_values = summary.set_index("annee")
    gap_rows = []
    if 2020 in yearly_values.index and 2014 in yearly_values.index:
        gap_rows.append(
            {
                "comparaison": "2020_vs_2014",
                "ecart_moyenne_points": round(
                    yearly_values.loc[2020, "mean"] - yearly_values.loc[2014, "mean"], 2
                ),
                "ecart_relatif_pct": round(
                    safe_divide(
                        pd.Series([yearly_values.loc[2020, "mean"] - yearly_values.loc[2014, "mean"]]),
                        pd.Series([yearly_values.loc[2014, "mean"]]),
                    ).iloc[0]
                    * 100,
                    2,
                ),
            }
        )
    if 2020 in yearly_values.index and 2026 in yearly_values.index:
        gap_rows.append(
            {
                "comparaison": "2020_vs_2026",
                "ecart_moyenne_points": round(
                    yearly_values.loc[2020, "mean"] - yearly_values.loc[2026, "mean"], 2
                ),
                "ecart_relatif_pct": round(
                    safe_divide(
                        pd.Series([yearly_values.loc[2020, "mean"] - yearly_values.loc[2026, "mean"]]),
                        pd.Series([yearly_values.loc[2026, "mean"]]),
                    ).iloc[0]
                    * 100,
                    2,
                ),
            }
        )
    relative_gaps = pd.DataFrame(gap_rows)

    index_columns = [
        column
        for column in ["code_commune", "nom_commune"]
        if column in df.columns
    ]
    tests_rows = []

    if index_columns:
        pivot = df.pivot_table(
            index=index_columns,
            columns="annee",
            values="taux_participation",
            aggfunc="mean",
        )

        for year_a, year_b in [(2014, 2020), (2020, 2026)]:
            if year_a not in pivot.columns or year_b not in pivot.columns:
                continue

            paired = pivot[[year_a, year_b]].dropna()
            if len(paired) < 10:
                continue

            t_stat, t_pvalue = ttest_rel(paired[year_a], paired[year_b], nan_policy="omit")
            try:
                w_stat, w_pvalue = wilcoxon(paired[year_a], paired[year_b])
            except ValueError:
                w_stat, w_pvalue = np.nan, np.nan

            tests_rows.append(
                {
                    "comparaison": f"{year_a}_vs_{year_b}",
                    "n_communes_appariees": int(len(paired)),
                    "difference_moyenne_points": round(
                        (paired[year_b] - paired[year_a]).mean(), 2
                    ),
                    "t_test_pvalue": round(float(t_pvalue), 6),
                    "wilcoxon_pvalue": (
                        round(float(w_pvalue), 6) if not pd.isna(w_pvalue) else np.nan
                    ),
                }
            )

    tests = pd.DataFrame(tests_rows)
    return {
        "summary": summary,
        "relative_gaps": relative_gaps,
        "tests": tests,
    }
