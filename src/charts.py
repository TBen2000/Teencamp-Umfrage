"""
Erzeugung aller Diagramme als hochauflösende PNGs.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from src.data_model import ROLE_TEEN, ROLE_STAFF, ROLE_PARENT, ROLE_OTHER
from src.analysis import (
    LIKERT_QUESTIONS,
    DROPOUT_EXPLANATION,
    would_likely_drop_out,
    other_role_breakdown,
    role_counts,
)

DPI = 200
ROLE_COLORS = {
    ROLE_TEEN: "#1f77b4",
    ROLE_PARENT: "#2ca02c",
    ROLE_STAFF: "#ff7f0e",
    ROLE_OTHER: "#7f7f7f",
}

ROLE_ORDER = [ROLE_TEEN, ROLE_PARENT, ROLE_STAFF, ROLE_OTHER]


def _other_legend_suffix(df: pd.DataFrame) -> str:
    breakdown = other_role_breakdown(df)
    if not breakdown:
        return ""
    parts = [f"{k} ({v})" for k, v in breakdown.items()]
    return "Sonstige umfasst: " + ", ".join(parts)


def _save(fig, output_dir: str, filename: str) -> str:
    path = os.path.join(output_dir, filename)
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def chart_likert_stacked_bar(df: pd.DataFrame, question_key: str, output_dir: str) -> str:
    """Gestapeltes Säulendiagramm 1-5, farblich nach Rolle aufgeteilt."""
    title = LIKERT_QUESTIONS[question_key]
    fig, ax = plt.subplots(figsize=(9, 6))

    values = [1, 2, 3, 4, 5]
    bottom = [0] * len(values)

    if not df.empty:
        for role in ROLE_ORDER:
            role_df = df[df["role"] == role]
            counts = [int((role_df[question_key] == v).sum()) for v in values]
            ax.bar(
                values,
                counts,
                bottom=bottom,
                label=role,
                color=ROLE_COLORS[role],
            )
            bottom = [b + c for b, c in zip(bottom, counts)]

    ax.set_xticks(values)
    ax.set_xlabel("Zustimmung (1 = überhaupt nicht, 5 = voll und ganz)")
    ax.set_ylabel("Anzahl Abstimmungen")
    ax.set_title(title, fontsize=12, wrap=True)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    suffix = _other_legend_suffix(df)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, title="Gruppe", loc="upper left")
    if suffix:
        fig.text(0.01, -0.05, suffix, fontsize=8, wrap=True)

    return _save(fig, output_dir, f"saeulendiagramm_{question_key}.png")


def chart_dropout_pie(df: pd.DataFrame, output_dir: str) -> str:
    fig, ax = plt.subplots(figsize=(9, 8))

    if df.empty:
        dropout_count, total = 0, 0
    else:
        dropout_mask = would_likely_drop_out(df)
        dropout_count = int(dropout_mask.sum())
        total = len(df)

    other_count = max(total - dropout_count, 0)

    if total == 0:
        ax.text(0.5, 0.5, "Keine Daten vorhanden", ha="center", va="center")
    else:
        ax.pie(
            [dropout_count, other_count],
            labels=[
                f"Würde höchstwahrscheinlich\nnicht mehr mitkommen ({dropout_count})",
                f"Übrige Teilnehmer ({other_count})",
            ],
            colors=["#d62728", "#c7c7c7"],
            autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
            startangle=90,
        )
    ax.set_title(
        "Anteil der Personen, die bei einer Verschiebung um 5 Tage\n"
        "höchstwahrscheinlich nicht mehr mitkommen würden",
        fontsize=12,
    )
    fig.text(
        0.5, -0.05, DROPOUT_EXPLANATION, ha="center", va="top", fontsize=8, wrap=True
    )
    return _save(fig, output_dir, "kuchendiagramm_dropout.png")


def chart_dropout_pie_by_group(df: pd.DataFrame, roles: list[str], group_label: str,
                                output_dir: str, filename: str) -> str:
    """Gleiche Auswertung, aber gefiltert auf eine bestimmte Rollen-Gruppe."""
    subset = df[df["role"].isin(roles)] if not df.empty else df
    fig, ax = plt.subplots(figsize=(9, 8))

    if subset.empty:
        ax.text(0.5, 0.5, "Keine Daten vorhanden", ha="center", va="center")
        dropout_count, total = 0, 0
    else:
        dropout_mask = would_likely_drop_out(subset)
        dropout_count = int(dropout_mask.sum())
        total = len(subset)
        other_count = max(total - dropout_count, 0)
        ax.pie(
            [dropout_count, other_count],
            labels=[
                f"Würde höchstwahrscheinlich\nnicht mehr mitkommen ({dropout_count})",
                f"Übrige ({other_count})",
            ],
            colors=["#d62728", "#c7c7c7"],
            autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
            startangle=90,
        )
    ax.set_title(
        f"Anteil 'nicht mehr mitkommend' – Gruppe: {group_label}", fontsize=12
    )
    fig.text(0.5, -0.05, DROPOUT_EXPLANATION, ha="center", va="top", fontsize=8, wrap=True)
    return _save(fig, output_dir, filename)


def chart_role_distribution_pie(df: pd.DataFrame, output_dir: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 8))
    counts = role_counts(df)
    if counts.empty:
        ax.text(0.5, 0.5, "Keine Daten vorhanden", ha="center", va="center")
    else:
        counts = counts.reindex(ROLE_ORDER).fillna(0)
        colors = [ROLE_COLORS[r] for r in counts.index]
        ax.pie(
            counts.values,
            labels=[f"{r} ({int(v)})" for r, v in counts.items()],
            colors=colors,
            autopct=lambda p: f"{p:.1f}%" if p > 0 else "",
            startangle=90,
        )
    ax.set_title("Verteilung der Teilnehmergruppen", fontsize=13)

    suffix = _other_legend_suffix(df)
    if suffix:
        fig.text(0.5, -0.05, suffix, ha="center", va="top", fontsize=8, wrap=True)

    return _save(fig, output_dir, "kuchendiagramm_rollenverteilung.png")


def chart_years_attended_of_dropouts(df: pd.DataFrame, output_dir: str) -> str:
    """
    Anzahl der Jahre (2024-2026), an denen die 'Dropout'-Gruppe teilgenommen hat.
    0 = an keinem der drei Jahre / widersprüchliche Angabe.
    """
    fig, ax = plt.subplots(figsize=(9, 6))

    if df.empty:
        ax.text(0.5, 0.5, "Keine Daten vorhanden", ha="center", va="center")
    else:
        dropout_df = df[would_likely_drop_out(df)]
        if dropout_df.empty:
            ax.text(0.5, 0.5, "Aktuell niemand in dieser Gruppe", ha="center", va="center")
        else:
            counts = dropout_df["years_count"].value_counts().reindex([0, 1, 2, 3], fill_value=0)
            labels = ["0 Jahre\n(bisher nicht dabei)", "1 Jahr", "2 Jahre", "3 Jahre\n(alle)"]
            bars = ax.bar(labels, counts.values, color="#9467bd")
            ax.bar_label(bars)

    ax.set_ylabel("Anzahl Personen")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.set_title(
        "Bisherige Teilnahme-Erfahrung (Anzahl Jahre 2024-2026)\n"
        "der Personen, die höchstwahrscheinlich nicht mehr mitkommen würden",
        fontsize=11,
    )
    fig.text(0.5, -0.08, DROPOUT_EXPLANATION, ha="center", va="top", fontsize=8, wrap=True)
    return _save(fig, output_dir, "diagramm_dropout_jahre.png")


def chart_years_participation_overview(df: pd.DataFrame, output_dir: str) -> str:
    """Übersicht, an wie vielen Jahren die Gesamtheit der Teilnehmer teilgenommen hat."""
    fig, ax = plt.subplots(figsize=(9, 6))
    if df.empty:
        ax.text(0.5, 0.5, "Keine Daten vorhanden", ha="center", va="center")
    else:
        bottom = [0] * 4
        for role in ROLE_ORDER:
            role_df = df[df["role"] == role]
            counts = [int((role_df["years_count"] == v).sum()) for v in [0, 1, 2, 3]]
            ax.bar(
                ["0 Jahre", "1 Jahr", "2 Jahre", "3 Jahre"],
                counts,
                bottom=bottom,
                label=role,
                color=ROLE_COLORS[role],
            )
            bottom = [b + c for b, c in zip(bottom, counts)]
        ax.legend(title="Gruppe")

    ax.set_ylabel("Anzahl Personen")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.set_title("Teilnahme-Erfahrung aller Befragten (Anzahl Jahre 2024-2026)", fontsize=12)
    suffix = _other_legend_suffix(df)
    if suffix:
        fig.text(0.5, -0.05, suffix, ha="center", va="top", fontsize=8, wrap=True)
    return _save(fig, output_dir, "diagramm_jahre_gesamtuebersicht.png")


def generate_all_charts(df: pd.DataFrame, output_dir: str) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    # Säulendiagramme für jede Likert-Frage
    for key in LIKERT_QUESTIONS:
        paths.append(chart_likert_stacked_bar(df, key, output_dir))

    # Kuchendiagramme zum "Dropout"
    paths.append(chart_dropout_pie(df, output_dir))
    paths.append(
        chart_dropout_pie_by_group(
            df, [ROLE_TEEN, ROLE_PARENT], "Teens + Eltern", output_dir,
            "kuchendiagramm_dropout_teens_eltern.png",
        )
    )
    paths.append(
        chart_dropout_pie_by_group(
            df, [ROLE_STAFF], "Mitarbeiter", output_dir,
            "kuchendiagramm_dropout_mitarbeiter.png",
        )
    )

    # Allgemeine Diagramme
    paths.append(chart_role_distribution_pie(df, output_dir))
    paths.append(chart_years_attended_of_dropouts(df, output_dir))
    paths.append(chart_years_participation_overview(df, output_dir))

    return paths