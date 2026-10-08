"""
Berechnung der inhaltlichen Kennzahlen, insbesondere der Gruppe der
"höchstwahrscheinlich nicht mehr Mitkommenden".
"""
import pandas as pd

from src.data_model import ROLE_TEEN, ROLE_STAFF, ROLE_PARENT, ROLE_OTHER


LIKERT_QUESTIONS = {
    "week4_fit": "Das Teencamp in der 4. Woche der Sommerferien ist für mich geschickt",
    "week4_plus5_fit": "5 Tage später wäre für mich geschickt",
    "attend_anyway": "Ich wäre auf jeden Fall dabei, unabhängig von der Terminlage",
    "more_days": "Ich würde mir MEHR als 7 Tage Teencamp wünschen",
    "less_days": "Ich würde mir WENIGER als 7 Tage Teencamp wünschen",
}


def would_likely_drop_out(df: pd.DataFrame) -> pd.Series:
    """
    Bedingung für "würde bei Verschiebung um 5 Tage höchstwahrscheinlich
    nicht mehr mitkommen":

      - week4_plus5_fit in {1, 2}
      - UND week4_fit >= week4_plus5_fit + 2
      - UND attend_anyway NICHT in {4, 5}  (d.h. in {1, 2, 3})
    """
    if df.empty:
        return pd.Series([], dtype=bool)

    cond = (
        df["week4_plus5_fit"].isin([1, 2])
        & (df["week4_fit"] >= df["week4_plus5_fit"] + 2)
        & (~df["attend_anyway"].isin([4, 5]))
    )
    return cond.fillna(False)


DROPOUT_EXPLANATION = (
    "Als 'höchstwahrscheinlich nicht mehr mitkommend' gelten Personen, die die "
    "Verschiebung um 5 Tage schlecht bewerten (1-2 Punkte), gleichzeitig die "
    "aktuelle 4. Woche spürbar besser bewerten (mindestens 2 Punkte höher) "
    "und nicht angegeben haben, sowieso auf jeden Fall dabei zu sein "
    "(Zustimmung 4-5 bei dieser Frage schließt sie aus)."
)


def role_subset(df: pd.DataFrame, roles: list[str]) -> pd.DataFrame:
    if df.empty:
        return df
    return df[df["role"].isin(roles)]


def other_role_breakdown(df: pd.DataFrame) -> dict:
    """Liefert die individuellen Freitexte der Gruppe 'Sonstige' für die Legende."""
    if df.empty:
        return {}
    others = df[df["role"] == ROLE_OTHER]
    texts = others["role_other_text"].dropna()
    texts = texts[texts.str.strip() != ""]
    counts = texts.value_counts().to_dict()
    unnamed = len(others) - sum(counts.values())
    if unnamed > 0:
        counts["(ohne Angabe)"] = unnamed
    return counts


def years_attended_breakdown(df_dropout: pd.DataFrame) -> pd.Series:
    """Anzahl Jahre (0,1,2,3) für die Dropout-Gruppe."""
    if df_dropout.empty:
        return pd.Series(dtype=int)
    return df_dropout["years_count"].value_counts().sort_index()


def role_counts(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=int)
    return df["role"].value_counts()