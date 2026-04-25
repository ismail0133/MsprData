"""Preparation du dataset ML, modeles simples et projection exploratoire 2032."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def prepare_ml_dataset(panel_df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute des variables explicatives simples a partir du panel."""

    if panel_df.empty:
        return panel_df.copy()

    working_df = panel_df.copy()
    group_column = "code_commune" if "code_commune" in working_df.columns else "nom_commune"
    for column in ["code_commune", "code_departement"]:
        if column in working_df.columns:
            working_df[column] = (
                working_df[column]
                .astype("string")
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )
            working_df.loc[working_df[column].isin(["<NA>", "nan", "None", ""]), column] = pd.NA
    working_df = working_df.sort_values([group_column, "annee"]).reset_index(drop=True)

    if "taux_participation" in working_df.columns:
        working_df["taux_participation_precedent"] = working_df.groupby(group_column)[
            "taux_participation"
        ].shift(1)
        working_df["variation_participation_precedente"] = working_df.groupby(group_column)[
            "taux_participation"
        ].diff()

    if "nombre_votants" in working_df.columns:
        working_df["nombre_votants_precedent"] = working_df.groupby(group_column)[
            "nombre_votants"
        ].shift(1)

    if "nombre_inscrits" in working_df.columns:
        working_df["nombre_inscrits_precedent"] = working_df.groupby(group_column)[
            "nombre_inscrits"
        ].shift(1)

    if {"nombre_inscrits", "population_totale"}.issubset(working_df.columns):
        working_df["ratio_inscrits_population"] = np.round(
            working_df["nombre_inscrits"] / working_df["population_totale"].replace(0, np.nan),
            4,
        )

    working_df["annees_depuis_2014"] = working_df["annee"] - 2014
    return working_df


def infer_feature_columns(df: pd.DataFrame, target_column: str) -> List[str]:
    """Selectionne des variables explicatives pertinentes en limitant les fuites."""

    excluded_columns = {
        target_column,
        "nom_commune",
        "code_commune",
        "periode_covid",
    }

    if target_column == "taux_participation":
        excluded_columns.update({"nombre_votants", "nombre_abstentions", "taux_abstention"})
    elif target_column == "nombre_votants":
        excluded_columns.update({"taux_participation", "taux_abstention", "nombre_abstentions"})

    preferred_features = [
        "annee",
        "annees_depuis_2014",
        "covid_2020",
        "code_departement",
        "population_totale",
        "taux_chomage",
        "nombre_chomeurs",
        "revenu_median",
        "taux_pauvrete",
        "nombre_faits",
        "taux_criminalite",
        "nombre_inscrits",
        "taux_participation_precedent",
        "variation_participation_precedente",
        "nombre_votants_precedent",
        "nombre_inscrits_precedent",
        "ratio_inscrits_population",
    ]

    feature_columns = [
        column
        for column in preferred_features
        if column in df.columns and column not in excluded_columns
    ]

    return feature_columns


def split_train_test(
    df: pd.DataFrame,
    feature_columns: List[str],
    target_column: str,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.DataFrame, pd.DataFrame]:
    """Separe train et test, de preference par commune pour limiter les fuites."""

    modelling_df = df.dropna(subset=[target_column]).copy()
    X = modelling_df[feature_columns].copy()
    y = modelling_df[target_column].copy()

    group_column = "code_commune" if "code_commune" in modelling_df.columns else "nom_commune"
    groups = None
    if group_column in modelling_df.columns:
        groups = modelling_df[group_column].astype("string").fillna("__missing_group__")

    if groups is not None and groups.nunique() >= 10:
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=random_state)
        train_index, test_index = next(splitter.split(X, y, groups=groups))
        train_frame = modelling_df.iloc[train_index].copy()
        test_frame = modelling_df.iloc[test_index].copy()
    else:
        train_frame, test_frame = train_test_split(
            modelling_df,
            test_size=0.2,
            random_state=random_state,
        )

    X_train = train_frame[feature_columns].copy()
    X_test = test_frame[feature_columns].copy()
    y_train = train_frame[target_column].copy()
    y_test = test_frame[target_column].copy()
    return X_train, X_test, y_train, y_test, train_frame, test_frame


def build_preprocessor(X: pd.DataFrame) -> Tuple[ColumnTransformer, List[str], List[str]]:
    """Construit le pipeline de pretraitement numerique et categoriel."""

    def is_categorical_feature(column: str) -> bool:
        series = X[column]
        if column.startswith("code_"):
            return True
        if pd.api.types.is_object_dtype(series):
            return True
        if pd.api.types.is_string_dtype(series):
            return True
        if pd.api.types.is_categorical_dtype(series):
            return True
        if pd.api.types.is_bool_dtype(series):
            return True
        return False

    categorical_features = [
        column
        for column in X.columns
        if is_categorical_feature(column)
    ]
    numeric_features = [column for column in X.columns if column not in categorical_features]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
    )
    return preprocessor, numeric_features, categorical_features


def build_sample_weights(
    df: pd.DataFrame,
    covid_weight: float = 0.5,
) -> np.ndarray:
    """Attribue un poids plus faible a l'annee 2020 si demande."""

    if "covid_2020" not in df.columns:
        return np.ones(len(df))

    return np.where(df["covid_2020"] == 1, covid_weight, 1.0)


def sample_training_frame(
    df: pd.DataFrame,
    max_rows: int,
    random_state: int = 42,
) -> pd.DataFrame:
    """Sous-echantillonne un grand panel en preservant au mieux les annees."""

    if len(df) <= max_rows:
        return df.copy()

    if "annee" not in df.columns:
        return df.sample(n=max_rows, random_state=random_state).copy()

    sampled_parts = []
    total_rows = len(df)

    for offset, (_, group) in enumerate(df.groupby("annee", dropna=False)):
        target_size = max(1, int(round(len(group) / total_rows * max_rows)))
        sampled_parts.append(
            group.sample(
                n=min(len(group), target_size),
                random_state=random_state + offset,
            )
        )

    sampled_df = pd.concat(sampled_parts, ignore_index=True)
    if len(sampled_df) > max_rows:
        sampled_df = sampled_df.sample(n=max_rows, random_state=random_state).copy()
    elif len(sampled_df) < max_rows:
        remaining = df.drop(index=sampled_df.index, errors="ignore")
        if not remaining.empty:
            extra = remaining.sample(
                n=min(max_rows - len(sampled_df), len(remaining)),
                random_state=random_state,
            )
            sampled_df = pd.concat([sampled_df, extra], ignore_index=True)

    return sampled_df.reset_index(drop=True)


def train_models_for_target(
    ml_df: pd.DataFrame,
    target_column: str,
    scenario_name: str,
    covid_weight: float = 0.5,
    exclude_2020: bool = False,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Entraine une regression lineaire et une random forest pour une cible."""

    scenario_df = ml_df.copy()
    if exclude_2020 and "annee" in scenario_df.columns:
        scenario_df = scenario_df[scenario_df["annee"] != 2020].copy()
    scenario_df = scenario_df.dropna(subset=[target_column]).copy()

    feature_columns = infer_feature_columns(scenario_df, target_column)
    if not feature_columns or scenario_df[target_column].dropna().shape[0] < 20:
        return pd.DataFrame(), {}

    X_train, X_test, y_train, y_test, train_frame, _ = split_train_test(
        scenario_df, feature_columns, target_column, random_state=random_state
    )
    preprocessor, _, _ = build_preprocessor(X_train)

    models = {
        "Regression lineaire": LinearRegression(),
        "Random forest": RandomForestRegressor(
            n_estimators=60,
            max_depth=14,
            max_features="sqrt",
            max_samples=0.35,
            min_samples_leaf=2,
            n_jobs=-1,
            random_state=random_state,
        ),
    }

    training_weights = build_sample_weights(train_frame, covid_weight=covid_weight)
    full_weights = build_sample_weights(scenario_df, covid_weight=covid_weight)

    results_rows = []
    fitted_models: Dict[str, Pipeline] = {}

    for model_name, estimator in models.items():
        fit_frame = train_frame.copy()
        final_fit_frame = scenario_df.copy()
        if model_name == "Random forest":
            fit_frame = sample_training_frame(
                train_frame,
                max_rows=30000,
                random_state=random_state,
            )
            final_fit_frame = sample_training_frame(
                scenario_df,
                max_rows=45000,
                random_state=random_state,
            )

        fit_X = fit_frame[feature_columns].copy()
        fit_y = fit_frame[target_column].copy()
        fit_weights = build_sample_weights(fit_frame, covid_weight=covid_weight)
        final_fit_weights = build_sample_weights(final_fit_frame, covid_weight=covid_weight)

        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("regressor", estimator),
            ]
        )
        pipeline.fit(fit_X, fit_y, regressor__sample_weight=fit_weights)
        predictions = pipeline.predict(X_test)

        rmse = float(np.sqrt(mean_squared_error(y_test, predictions)))
        mae = float(mean_absolute_error(y_test, predictions))
        r2 = float(r2_score(y_test, predictions))

        results_rows.append(
            {
                "scenario": scenario_name,
                "cible": target_column,
                "modele": model_name,
                "mae": round(mae, 3),
                "rmse": round(rmse, 3),
                "r2": round(r2, 3),
                "n_train": int(len(fit_X)),
                "n_test": int(len(X_test)),
                "n_features": int(len(feature_columns)),
            }
        )

        final_pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("regressor", estimator.__class__(**estimator.get_params())),
            ]
        )
        final_pipeline.fit(
            final_fit_frame[feature_columns],
            final_fit_frame[target_column],
            regressor__sample_weight=final_fit_weights,
        )
        fitted_models[model_name] = final_pipeline

    results_df = pd.DataFrame(results_rows).sort_values(["rmse", "mae"]).reset_index(drop=True)
    bundle = {
        "scenario": scenario_name,
        "target": target_column,
        "features": feature_columns,
        "models": fitted_models,
        "data": scenario_df.copy(),
    }
    return results_df, bundle


def compare_model_scenarios(
    ml_df: pd.DataFrame,
    target_column: str,
    covid_weight: float = 0.5,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, Dict[str, object]]]:
    """Compare trois strategies de prise en compte de 2020."""

    scenario_settings = {
        "avec_covid": {"covid_weight": 1.0, "exclude_2020": False},
        "covid_pondere": {"covid_weight": covid_weight, "exclude_2020": False},
        "sans_2020": {"covid_weight": 1.0, "exclude_2020": True},
    }

    results_tables = []
    bundles: Dict[str, Dict[str, object]] = {}

    for scenario_name, settings in scenario_settings.items():
        results_df, bundle = train_models_for_target(
            ml_df=ml_df,
            target_column=target_column,
            scenario_name=scenario_name,
            covid_weight=settings["covid_weight"],
            exclude_2020=settings["exclude_2020"],
            random_state=random_state,
        )
        if not results_df.empty:
            results_tables.append(results_df)
            bundles[scenario_name] = bundle

    if not results_tables:
        return pd.DataFrame(), bundles

    combined_results = pd.concat(results_tables, ignore_index=True)
    combined_results = combined_results.sort_values(
        ["rmse", "mae", "scenario", "modele"]
    ).reset_index(drop=True)
    return combined_results, bundles


def create_projection_frame(ml_df: pd.DataFrame, projection_year: int = 2032) -> pd.DataFrame:
    """Construit un jeu de donnees 2032 en prolongeant le dernier etat connu.

    Cette projection est exploratoire :
    elle suppose que les variables contextuelles restent au dernier niveau observe.
    """

    if ml_df.empty:
        return ml_df.copy()

    group_column = "code_commune" if "code_commune" in ml_df.columns else "nom_commune"
    latest = (
        ml_df.sort_values([group_column, "annee"])
        .groupby(group_column, as_index=False)
        .tail(1)
        .copy()
    )

    if "taux_participation" in latest.columns and "taux_participation_precedent" in latest.columns:
        latest["taux_participation_precedent"] = latest["taux_participation"]

    if "nombre_votants" in latest.columns and "nombre_votants_precedent" in latest.columns:
        latest["nombre_votants_precedent"] = latest["nombre_votants"]

    if "nombre_inscrits" in latest.columns and "nombre_inscrits_precedent" in latest.columns:
        latest["nombre_inscrits_precedent"] = latest["nombre_inscrits"]

    latest["annee"] = projection_year
    latest["annees_depuis_2014"] = projection_year - 2014
    latest["covid_2020"] = 0

    for target_column in ["nombre_votants", "taux_participation"]:
        if target_column in latest.columns:
            latest[target_column] = np.nan

    return latest.reset_index(drop=True)


def generate_projection_2032(
    ml_df: pd.DataFrame,
    bundles: Dict[str, Dict[str, object]],
    target_column: str,
    projection_year: int = 2032,
    preferred_scenario: str = "covid_pondere",
) -> pd.DataFrame:
    """Genere une projection communale 2032 a partir du meilleur modele disponible."""

    if not bundles:
        return pd.DataFrame()

    scenario_name = preferred_scenario if preferred_scenario in bundles else next(iter(bundles))
    bundle = bundles[scenario_name]
    projection_frame = create_projection_frame(ml_df, projection_year=projection_year)
    feature_columns = bundle["features"]

    available_models = bundle["models"]
    model_name = "Random forest" if "Random forest" in available_models else next(iter(available_models))
    model = available_models[model_name]

    missing_features = [column for column in feature_columns if column not in projection_frame.columns]
    for column in missing_features:
        projection_frame[column] = np.nan

    prediction_values = model.predict(projection_frame[feature_columns])
    prediction_column = f"prediction_{target_column}_{projection_year}"

    output_columns = [
        column
        for column in ["code_commune", "nom_commune", "code_departement", "annee"]
        if column in projection_frame.columns
    ]
    output_df = projection_frame[output_columns].copy()
    output_df["scenario"] = scenario_name
    output_df["modele"] = model_name
    output_df[prediction_column] = np.round(prediction_values, 2)
    return output_df
