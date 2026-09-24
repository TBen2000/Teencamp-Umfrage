"""
Wandelt die rohen Nextcloud-Forms-Antworten in ein sauberes DataFrame um.

Die Fragezuordnung erfolgt über Teilwort-Matching auf robuste,
eindeutige Schlagworte (falls sich Formulierungen leicht ändern).
"""
import hashlib
import json
import pandas as pd

# Schlagwörter, die eindeutig genug sind, um die jeweilige Frage zu identifizieren.
QUESTION_KEYWORDS = {
    "role": "ich bin",
    "years": "teencamps dabei",
    "week4_fit": "vierten woche",
    "week4_plus5_fit": "fünf tage später",
    "attend_anyway": "auf jeden fall auf dem teencamp",
    "more_days": "mehr als sieben tage",
    "less_days": "weniger als sieben tage",
    "remarks": "weitere anmerkungen",
}

ROLE_TEEN = "Teen"
ROLE_STAFF = "Mitarbeiter"
ROLE_PARENT = "Elternteil"
ROLE_OTHER = "Sonstige"


def _match_question_id(questions: list[dict], keyword: str) -> str | None:
    keyword = keyword.lower()
    matches = [q for q in questions if keyword in q.get("text", "").lower()]
    if len(matches) == 1:
        return str(matches[0]["id"])
    if len(matches) > 1:
        # Nimm den kürzesten Text als wahrscheinlichsten eindeutigen Treffer
        matches.sort(key=lambda q: len(q.get("text", "")))
        return str(matches[0]["id"])
    return None


def build_question_map(form_definition: dict) -> dict:
    questions = form_definition.get("questions", [])
    qmap = {}
    for key, keyword in QUESTION_KEYWORDS.items():
        qid = _match_question_id(questions, keyword)
        if qid is None:
            raise ValueError(
                f"Frage für Schlüssel '{key}' (Keyword '{keyword}') konnte nicht "
                "gefunden werden. Wurde der Fragetext im Formular stark verändert?"
            )
        qmap[key] = qid
    return qmap


def _extract_answer_texts(answers: list[dict], question_id: str) -> list[str]:
    return [a["text"] for a in answers if str(a.get("questionId")) == str(question_id)]


def _parse_role(raw_texts: list[str]) -> tuple[str, str | None]:
    if not raw_texts:
        return ROLE_OTHER, None
    text = raw_texts[0].strip()
    lower = text.lower()
    if lower == "teen":
        return ROLE_TEEN, None
    if lower == "mitarbeiter":
        return ROLE_STAFF, None
    if lower == "elternteil":
        return ROLE_PARENT, None
    # "Andere" mit Freitext -> der eingegebene Text selbst ist die Antwort
    return ROLE_OTHER, text if text else None


def _parse_years(raw_texts: list[str]) -> set[str]:
    return set(t.strip() for t in raw_texts)


def _years_attended_count(years: set[str]) -> int:
    """
    Anzahl der Jahre 2024-2026, an denen jemand dabei war.
    Enthält die Antwortmenge zusätzlich "Auf keinem der drei", gilt das als
    widersprüchlich -> wir werten es dann als 0 (nicht dabei gewesen).
    """
    valid_years = {"2024", "2025", "2026"}
    if "Auf keinem der drei" in years:
        return 0
    return len(years & valid_years)


def _to_int(raw_texts: list[str]) -> int | None:
    if not raw_texts:
        return None
    try:
        return int(raw_texts[0])
    except (ValueError, TypeError):
        return None


def submissions_to_dataframe(submissions: dict, question_map: dict) -> pd.DataFrame:
    rows = []
    for sub in submissions.get("submissions", []):
        answers = sub.get("answers", [])

        role_raw = _extract_answer_texts(answers, question_map["role"])
        role, role_other_text = _parse_role(role_raw)

        years_raw = _extract_answer_texts(answers, question_map["years"])
        years = _parse_years(years_raw)

        row = {
            "submission_id": sub.get("id"),
            "timestamp": sub.get("timestamp"),
            "role": role,
            "role_other_text": role_other_text,
            "years": sorted(years),
            "years_count": _years_attended_count(years),
            "week4_fit": _to_int(_extract_answer_texts(answers, question_map["week4_fit"])),
            "week4_plus5_fit": _to_int(
                _extract_answer_texts(answers, question_map["week4_plus5_fit"])
            ),
            "attend_anyway": _to_int(
                _extract_answer_texts(answers, question_map["attend_anyway"])
            ),
            "more_days": _to_int(_extract_answer_texts(answers, question_map["more_days"])),
            "less_days": _to_int(_extract_answer_texts(answers, question_map["less_days"])),
            "remarks": (
                _extract_answer_texts(answers, question_map["remarks"])[0]
                if _extract_answer_texts(answers, question_map["remarks"])
                else ""
            ),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True).dt.tz_convert(
            "Europe/Berlin"
        )
        df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def compute_data_fingerprint(df: pd.DataFrame) -> str:
    """
    Erzeugt einen stabilen Hash über die relevanten Daten, um Änderungen
    zwischen zwei Durchläufen zu erkennen (Neu, geändert, gelöscht).
    """
    if df.empty:
        payload = "EMPTY"
    else:
        cols = [c for c in df.columns if c != "timestamp"]
        payload = df[cols].to_json(orient="records", force_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()