"""Visualisations academiques pour l'analyse electorale communale."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


ACADEMIC_PALETTE = {
    2014: "#1f4e79",
    2020: "#a63d40",
    2026: "#5b8e55",
}
DEFAULT_YEAR_COLOR = "#6b7280"


LABELS = {
    "taux_participation": "Taux de participation (%)",
    "nombre_votants": "Nombre de votants",
    "population_totale": "Population totale",
    "taux_chomage": "Taux de chomage (%)",
    "revenu_median": "Revenu median",
    "taux_pauvrete": "Taux de pauvrete (%)",
    "nombre_faits": "Nombre de faits",
    "taux_criminalite": "Taux de criminalite",
}


def set_academic_style() -> None:
    """Applique un style sobre adapte a une presentation universitaire."""

    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.figsize": (12, 7),
            "axes.titlesize": 16,
            "axes.labelsize": 13,
            "legend.fontsize": 11,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def ensure_output_dir(output_path: Path | str | None) -> Path | None:
    """Cree le dossier de sortie si necessaire."""

    if output_path is None:
        return None

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_figure(fig: plt.Figure, output_path: Path | str | None = None) -> None:
    """Enregistre proprement une figure."""

    path = ensure_output_dir(output_path)
    fig.tight_layout()
    if path is not None:
        fig.savefig(path, dpi=300, bbox_inches="tight")


def prepare_year_plot_data(
    df: pd.DataFrame,
    required_columns: Iterable[str],
) -> tuple[pd.DataFrame, list[str], dict[str, str]]:
    """Normalise la variable annee pour des palettes stables avec seaborn."""

    plot_df = df.dropna(subset=list(required_columns)).copy()
    plot_df["annee"] = pd.to_numeric(plot_df["annee"], errors="coerce")
    plot_df = plot_df.dropna(subset=["annee"]).copy()
    plot_df["annee"] = plot_df["annee"].astype(int)
    plot_df["annee_label"] = plot_df["annee"].astype(str)

    year_order = [str(year) for year in sorted(plot_df["annee"].unique())]
    palette = {
        year_label: ACADEMIC_PALETTE.get(int(year_label), DEFAULT_YEAR_COLOR)
        for year_label in year_order
    }
    return plot_df, year_order, palette


def plot_histogram_by_year(
    df: pd.DataFrame,
    column: str,
    output_path: Path | str | None = None,
    bins: int = 30,
) -> tuple[plt.Figure, plt.Axes]:
    """Histogramme d'une variable par annee."""

    set_academic_style()
    plot_df, year_order, palette = prepare_year_plot_data(df, ["annee", column])
    fig, ax = plt.subplots()

    sns.histplot(
        data=plot_df,
        x=column,
        hue="annee_label",
        hue_order=year_order,
        bins=bins,
        element="step",
        stat="density",
        common_norm=False,
        palette=palette,
        ax=ax,
    )

    ax.set_title(f"Distribution du {LABELS.get(column, column)} par annee")
    ax.set_xlabel(LABELS.get(column, column))
    ax.set_ylabel("Densite")
    save_figure(fig, output_path)
    return fig, ax


def plot_boxplot_by_year(
    df: pd.DataFrame,
    column: str,
    output_path: Path | str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Boxplot d'une variable par annee."""

    set_academic_style()
    plot_df, year_order, palette = prepare_year_plot_data(df, ["annee", column])
    fig, ax = plt.subplots()

    sns.boxplot(
        data=plot_df,
        x="annee_label",
        y=column,
        order=year_order,
        hue="annee_label",
        dodge=False,
        legend=False,
        palette=palette,
        ax=ax,
    )

    ax.set_title(f"Dispersion du {LABELS.get(column, column)} par annee")
    ax.set_xlabel("Annee")
    ax.set_ylabel(LABELS.get(column, column))
    save_figure(fig, output_path)
    return fig, ax


def plot_yearly_mean_line(
    df: pd.DataFrame,
    metric: str,
    output_path: Path | str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Courbe de moyenne annuelle."""

    set_academic_style()
    summary = (
        df.dropna(subset=["annee", metric])
        .groupby("annee", as_index=False)[metric]
        .mean()
        .sort_values("annee")
    )
    summary["annee"] = pd.to_numeric(summary["annee"], errors="coerce")
    summary = summary.dropna(subset=["annee"]).copy()
    summary["annee"] = summary["annee"].astype(int)
    summary["annee_label"] = summary["annee"].astype(str)
    year_order = [str(year) for year in sorted(summary["annee"].unique())]
    palette = {
        year_label: ACADEMIC_PALETTE.get(int(year_label), DEFAULT_YEAR_COLOR)
        for year_label in year_order
    }

    fig, ax = plt.subplots()
    sns.lineplot(
        data=summary,
        x="annee",
        y=metric,
        marker="o",
        linewidth=2.5,
        color="#1f1f1f",
        ax=ax,
    )
    sns.scatterplot(
        data=summary,
        x="annee",
        y=metric,
        hue="annee_label",
        hue_order=year_order,
        palette=palette,
        legend=False,
        s=120,
        ax=ax,
    )

    for _, row in summary.iterrows():
        ax.text(
            row["annee"],
            row[metric],
            f"{row[metric]:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax.set_title(f"Evolution moyenne du {LABELS.get(metric, metric)}")
    ax.set_xlabel("Annee")
    ax.set_ylabel(LABELS.get(metric, metric))
    save_figure(fig, output_path)
    return fig, ax


def plot_scatter_relationship(
    df: pd.DataFrame,
    x_column: str,
    y_column: str,
    output_path: Path | str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Nuage de points avec droite de tendance globale."""

    set_academic_style()
    plot_df, year_order, palette = prepare_year_plot_data(
        df, [x_column, y_column, "annee"]
    )
    fig, ax = plt.subplots()

    sns.scatterplot(
        data=plot_df,
        x=x_column,
        y=y_column,
        hue="annee_label",
        hue_order=year_order,
        palette=palette,
        alpha=0.7,
        ax=ax,
    )
    sns.regplot(
        data=plot_df,
        x=x_column,
        y=y_column,
        scatter=False,
        color="#2b2b2b",
        line_kws={"linewidth": 2, "linestyle": "--"},
        ax=ax,
    )

    ax.set_title(
        f"Relation entre {LABELS.get(x_column, x_column).lower()} et {LABELS.get(y_column, y_column).lower()}"
    )
    ax.set_xlabel(LABELS.get(x_column, x_column))
    ax.set_ylabel(LABELS.get(y_column, y_column))
    save_figure(fig, output_path)
    return fig, ax


def plot_correlation_heatmap(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    output_path: Path | str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Carte de correlation des variables numeriques."""

    set_academic_style()
    if columns is None:
        numeric_df = df.select_dtypes(include=[np.number]).copy()
    else:
        selected_columns = [column for column in columns if column in df.columns]
        numeric_df = df[selected_columns].select_dtypes(include=[np.number]).copy()

    fig, ax = plt.subplots(figsize=(12, 9))
    if numeric_df.empty or numeric_df.shape[1] < 2:
        ax.set_title("Heatmap de correlation indisponible")
        ax.text(
            0.5,
            0.5,
            "Pas assez de variables numeriques pour calculer une correlation.",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax.axis("off")
        save_figure(fig, output_path)
        return fig, ax

    correlation = numeric_df.corr()

    sns.heatmap(
        correlation,
        cmap="Blues",
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        cbar_kws={"label": "Coefficient de correlation"},
        ax=ax,
    )
    ax.set_title("Heatmap de correlation des variables numeriques")
    save_figure(fig, output_path)
    return fig, ax


def plot_top_communes_bar(
    variation_df: pd.DataFrame,
    output_path: Path | str | None = None,
    title: str = "",
    n: int = 10,
    ascending: bool = True,
) -> tuple[plt.Figure, plt.Axes]:
    """Bar chart horizontal pour les variations communales les plus fortes."""

    set_academic_style()
    plot_df = variation_df.copy()
    if plot_df.empty:
        fig, ax = plt.subplots()
        ax.set_title(title or "Aucune variation disponible")
        return fig, ax

    plot_df = plot_df.sort_values("variation_absolue", ascending=ascending).head(n)
    commune_label = (
        plot_df["nom_commune"]
        if "nom_commune" in plot_df.columns
        else plot_df["code_commune"].astype(str)
    )
    plot_df = plot_df.assign(libelle_commune=commune_label)

    colors = ["#a63d40" if value < 0 else "#5b8e55" for value in plot_df["variation_absolue"]]
    fig, ax = plt.subplots(figsize=(12, 8))

    sns.barplot(
        data=plot_df,
        x="variation_absolue",
        y="libelle_commune",
        palette=colors,
        ax=ax,
    )
    ax.set_title(title)
    ax.set_xlabel("Variation du taux de participation (points)")
    ax.set_ylabel("Commune")
    save_figure(fig, output_path)
    return fig, ax


def plot_2020_anomaly(
    summary_df: pd.DataFrame,
    output_path: Path | str | None = None,
) -> tuple[plt.Figure, plt.Axes]:
    """Graphique mettant en evidence l'atypicite de 2020."""

    set_academic_style()
    plot_df = summary_df.copy()
    fig, ax = plt.subplots()

    sns.lineplot(
        data=plot_df,
        x="annee",
        y="mean",
        marker="o",
        linewidth=2.5,
        color="#1f4e79",
        label="Moyenne",
        ax=ax,
    )
    sns.lineplot(
        data=plot_df,
        x="annee",
        y="median",
        marker="s",
        linewidth=2.0,
        color="#5b8e55",
        label="Mediane",
        ax=ax,
    )

    if 2020 in plot_df["annee"].values:
        anomaly_row = plot_df.loc[plot_df["annee"] == 2020].iloc[0]
        ax.scatter([2020], [anomaly_row["mean"]], color="#a63d40", s=180, zorder=5)
        ax.axvline(2020, color="#a63d40", linestyle="--", linewidth=1.5, alpha=0.8)
        ax.text(
            2020,
            anomaly_row["mean"],
            "  Anomalie 2020",
            color="#a63d40",
            fontsize=11,
            va="bottom",
        )

    ax.set_title("Mise en evidence de l'anomalie de participation en 2020")
    ax.set_xlabel("Annee")
    ax.set_ylabel("Taux de participation (%)")
    save_figure(fig, output_path)
    return fig, ax
