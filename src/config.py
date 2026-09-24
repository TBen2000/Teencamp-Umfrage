"""
Zentrale Konfiguration über Umgebungsvariablen.
"""
import os
import sys
from dataclasses import dataclass


@dataclass
class Config:
    nc_url: str
    nc_user: str
    nc_password: str
    form_link: str | None
    form_name: str | None
    target_folder: str
    interval_minutes: int
    verify_tls: bool

    @staticmethod
    def from_env() -> "Config":
        nc_url = os.environ.get("NC_URL", "").rstrip("/")
        nc_user = os.environ.get("NC_USER", "")
        nc_password = os.environ.get("NC_PASSWORD", "")
        password_file = os.environ.get("NC_PASSWORD_FILE")
        if password_file and not nc_password:
            with open(password_file, "r", encoding="utf-8") as f:
                nc_password = f.read().strip()

        form_link = os.environ.get("NC_FORM_LINK") or None
        form_name = os.environ.get("NC_FORM_NAME") or None
        target_folder = os.environ.get("NC_TARGET_FOLDER", "/TeenCamp-Auswertung")
        interval_minutes = int(os.environ.get("INTERVAL_MINUTES", "15"))
        verify_tls = os.environ.get("VERIFY_TLS", "true").lower() != "false"

        errors = []
        if not nc_url:
            errors.append("NC_URL fehlt")
        if not nc_user:
            errors.append("NC_USER fehlt")
        if not nc_password:
            errors.append("NC_PASSWORD (oder NC_PASSWORD_FILE) fehlt")
        if not form_link and not form_name:
            errors.append("NC_FORM_LINK oder NC_FORM_NAME muss gesetzt sein")

        if errors:
            print("Konfigurationsfehler:", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            sys.exit(1)

        return Config(
            nc_url=nc_url,
            nc_user=nc_user,
            nc_password=nc_password,
            form_link=form_link,
            form_name=form_name,
            target_folder=target_folder if target_folder.startswith("/") else f"/{target_folder}",
            interval_minutes=interval_minutes,
            verify_tls=verify_tls,
        )