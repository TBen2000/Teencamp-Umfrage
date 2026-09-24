"""
Zugriff auf die Nextcloud Forms OCS-API (v3, aktuelle stabile Version).

Dieses Modul ist bewusst auf EINE spezielle Umfrage zugeschnitten und
kümmert sich um nichts anderes (kein Multi-Formular-Handling nötig).
"""
import re
import time
import requests

OCS_HEADERS = {"OCS-APIRequest": "true", "Accept": "application/json"}


class LoginError(Exception):
    pass


class FormNotFoundError(Exception):
    pass


class NextcloudFormsClient:
    def __init__(self, base_url: str, user: str, password: str, verify_tls: bool = True):
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.verify_tls = verify_tls
        self.session = requests.Session()
        self.session.auth = (user, password)
        self.session.headers.update(OCS_HEADERS)
        self._backoff = 5

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        resp = self.session.request(method, url, verify=self.verify_tls, timeout=30, **kwargs)
        if resp.status_code == 401:
            print(
                f"WARNUNG: Login fehlgeschlagen (401). Warte {self._backoff}s um "
                f"Brute-Force-Schutz nicht auszulösen. Bitte NC_USER/NC_PASSWORD prüfen!"
            )
            time.sleep(self._backoff)
            self._backoff = min(self._backoff * 2, 300)
            raise LoginError("Nextcloud-Login fehlgeschlagen (401 Unauthorized)")
        self._backoff = 5
        resp.raise_for_status()
        return resp

    @staticmethod
    def _extract_hash_from_link(link: str) -> str | None:
        # Erwartetes Format: https://host/index.php/apps/forms/s/<hash> oder .../apps/forms/<hash>
        m = re.search(r"/apps/forms/(?:s/)?([A-Za-z0-9_-]+)", link)
        return m.group(1) if m else None

    def _list_forms(self) -> list[dict]:
        resp = self._request(
            "GET", "/ocs/v2.php/apps/forms/api/v3/forms", params={"format": "json"}
        )
        data = resp.json()
        return data.get("ocs", {}).get("data", [])

    def find_form(self, form_link: str | None, form_name: str | None) -> dict:
        """
        Sucht das Formular primär über den Link (Hash), sekundär über den Namen.
        """
        forms = self._list_forms()

        if form_link:
            form_hash = self._extract_hash_from_link(form_link)
            if form_hash:
                for f in forms:
                    if f.get("hash") == form_hash:
                        return f
            print(
                "WARNUNG: Formular über NC_FORM_LINK nicht gefunden, "
                "versuche es über NC_FORM_NAME."
            )

        if form_name:
            name_lower = form_name.strip().lower()
            # Exakter Treffer zuerst
            exact = [f for f in forms if f.get("title", "").strip().lower() == name_lower]
            if len(exact) == 1:
                return exact[0]
            if len(exact) > 1:
                raise FormNotFoundError(
                    f"Mehrere Formulare mit dem exakten Titel '{form_name}' gefunden. "
                    "Bitte NC_FORM_LINK verwenden, um eindeutig zu sein."
                )
            # Teilwort-Matching als Fallback
            partial = [f for f in forms if name_lower in f.get("title", "").strip().lower()]
            if len(partial) == 1:
                return partial[0]
            if len(partial) > 1:
                titles = ", ".join(f"'{f.get('title')}'" for f in partial)
                raise FormNotFoundError(
                    f"Mehrere Formulare passen zu '{form_name}': {titles}. "
                    "Bitte NC_FORM_LINK oder einen eindeutigeren NC_FORM_NAME angeben."
                )

        raise FormNotFoundError(
            "Kein passendes Formular gefunden. Bitte NC_FORM_LINK oder NC_FORM_NAME prüfen. "
            "Der angegebene Account muss Besitzer des Formulars sein."
        )

    def get_full_form(self, form_id: int) -> dict:
        resp = self._request(
            "GET",
            f"/ocs/v2.php/apps/forms/api/v3/forms/{form_id}",
            params={"format": "json"},
        )
        return resp.json().get("ocs", {}).get("data", {})

    def get_submissions(self, form_id: int) -> dict:
        resp = self._request(
            "GET",
            f"/ocs/v2.php/apps/forms/api/v3/forms/{form_id}/submissions",
            params={"format": "json"},
        )
        return resp.json().get("ocs", {}).get("data", {})