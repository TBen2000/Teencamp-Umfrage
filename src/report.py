"""
Erzeugt eine Markdown-Datei mit allen Antworten, die eine Anmerkung enthalten.
Enthält bewusst KEINE Nutzerkennungen (Formular ist anonym, aber sicher ist sicher).
"""
import pandas as pd

from src.analysis import LIKERT_QUESTIONS


def _format_row(row: pd.Series) -> str:
    ts = row["timestamp"].strftime("%d.%m.%Y %H:%M") if pd.notna(row["timestamp"]) else "unbekannt"
    role = row["role"]
    if role == "Sonstige" and row.get("role_other_text"):
        role = f"Sonstige ({row['role_other_text']})"

    years = ", ".join(row["years"]) if row["years"] else "keine Angabe"

    lines = [
        f"### Eintrag vom {ts}",
        "",
        f"- **Rolle:** {role}",
        f"- **Teilgenommen an:** {years}",
    ]
    for key, label in LIKERT_QUESTIONS.items():
        value = row.get(key)
        lines.append(f"- **{label}:** {value if pd.notna(value) else 'keine Angabe'}")

    lines.append("")
    lines.append(f"> {row['remarks'].strip()}")
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def build_markdown_report(df: pd.DataFrame) -> str:
    header = [
        "# Anmerkungen aus der TeenCamp-Terminumfrage",
        "",
        "Diese Datei listet alle Umfrage-Einträge auf, bei denen eine Anmerkung",
        "im Freitextfeld gemacht wurde. Sortiert nach Zeitpunkt der Abgabe.",
        "Aus Datenschutzgründen werden keine Nutzerkennungen aufgeführt.",
        "",
    ]

    if df.empty:
        header.append("_Keine Daten vorhanden._")
        return "\n".join(header)

    with_remarks = df[df["remarks"].str.strip() != ""].sort_values("timestamp")

    if with_remarks.empty:
        header.append("_Es wurden bisher keine Anmerkungen abgegeben._")
        return "\n".join(header)

    body = [_format_row(row) for _, row in with_remarks.iterrows()]
    return "\n".join(header) + "\n" + "\n".join(body)