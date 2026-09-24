"""
Hauptprogramm:
1. Formular in Nextcloud finden (primär über Link, sekundär über Namen)
2. Ergebnisse herunterladen
3. Bei Datenänderung: Diagramme + Markdown-Report erzeugen und hochladen
4. Sonst: nur Last_Updated.txt aktualisieren
5. Alle N Minuten wiederholen (Endlosschleife im Container)

WICHTIG: Dieses Skript ist bewusst auf GENAU EINE spezielle Umfrage
(TeenCamp-Terminumfrage) zugeschnitten und kümmert sich um nichts anderes.
"""
import os
import shutil
import tempfile
import time
import traceback
from datetime import datetime
from zoneinfo import ZoneInfo

from src.config import Config
from src.nextcloud_forms import NextcloudFormsClient, LoginError, FormNotFoundError
from src.webdav_client import WebDAVClient
from src.data_model import build_question_map, submissions_to_dataframe, compute_data_fingerprint
from src.charts import generate_all_charts
from src.report import build_markdown_report

BERLIN_TZ = ZoneInfo("Europe/Berlin")


def now_berlin_str() -> str:
    return datetime.now(BERLIN_TZ).strftime("%d.%m.%Y %H:%M")


def write_last_updated(webdav: WebDAVClient, target_folder: str, data_changed: bool,
                        last_data_change_str: str | None) -> None:
    lines = ["Last updated:", now_berlin_str()]
    if last_data_change_str:
        lines.append("")
        lines.append("Letzte Datenänderung:")
        lines.append(last_data_change_str)
    content = "\n".join(lines) + "\n"
    webdav.upload_bytes(content.encode("utf-8"), target_folder, "Last_Updated.txt")


def run_once(config: Config, forms_client: NextcloudFormsClient, webdav: WebDAVClient,
             last_fingerprint: str | None, last_data_change_str: str | None):
    form_meta = forms_client.find_form(config.form_link, config.form_name)
    form_id = form_meta["id"]

    form_definition = forms_client.get_full_form(form_id)
    question_map = build_question_map(form_definition)

    submissions = forms_client.get_submissions(form_id)
    df = submissions_to_dataframe(submissions, question_map)

    fingerprint = compute_data_fingerprint(df)
    data_changed = fingerprint != last_fingerprint

    if not data_changed and last_fingerprint is not None:
        print("Keine Datenänderung erkannt. Aktualisiere nur Last_Updated.txt.")
        write_last_updated(webdav, config.target_folder, False, last_data_change_str)
        return fingerprint, last_data_change_str

    print(f"Datenänderung erkannt (oder erster Lauf). {len(df)} Antworten gefunden.")

    tmp_dir = tempfile.mkdtemp(prefix="teencamp_charts_")
    try:
        chart_paths = generate_all_charts(df, tmp_dir)
        for path in chart_paths:
            filename = os.path.basename(path)
            webdav.upload_file(path, config.target_folder, filename)
            print(f"Hochgeladen: {filename}")

        report_md = build_markdown_report(df)
        report_path = os.path.join(tmp_dir, "Anmerkungen.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
        webdav.upload_file(report_path, config.target_folder, "Anmerkungen.md")
        print("Hochgeladen: Anmerkungen.md")

        new_change_str = now_berlin_str()
        write_last_updated(webdav, config.target_folder, True, new_change_str)
        return fingerprint, new_change_str
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main():
    config = Config.from_env()

    forms_client = NextcloudFormsClient(
        config.nc_url, config.nc_user, config.nc_password, config.verify_tls
    )
    webdav = WebDAVClient(config.nc_url, config.nc_user, config.nc_password, config.verify_tls)

    last_fingerprint = None
    last_data_change_str = None

    print(
        f"Starte TeenCamp-Umfrage-Auswertung. Intervall: {config.interval_minutes} Minuten. "
        f"Zielordner: {config.target_folder}"
    )

    while True:
        try:
            last_fingerprint, last_data_change_str = run_once(
                config, forms_client, webdav, last_fingerprint, last_data_change_str
            )
        except LoginError as e:
            print(f"FEHLER (Login): {e}")
        except FormNotFoundError as e:
            print(f"FEHLER (Formular nicht gefunden): {e}")
        except Exception:
            print("Unerwarteter Fehler:")
            traceback.print_exc()

        time.sleep(max(config.interval_minutes, 1) * 60)


if __name__ == "__main__":
    main()