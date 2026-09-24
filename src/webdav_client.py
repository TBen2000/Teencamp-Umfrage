"""
Minimaler WebDAV-Client für Nextcloud (Upload + Ordner anlegen).
"""
import requests
from urllib.parse import quote


class WebDAVClient:
    def __init__(self, base_url: str, user: str, password: str, verify_tls: bool = True):
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.verify_tls = verify_tls
        self.session = requests.Session()
        self.session.auth = (user, password)
        self.dav_root = f"{self.base_url}/remote.php/dav/files/{quote(user)}"

    def _url(self, remote_path: str) -> str:
        remote_path = remote_path.strip("/")
        parts = [quote(p) for p in remote_path.split("/") if p]
        return f"{self.dav_root}/" + "/".join(parts)

    def ensure_folder(self, folder_path: str) -> None:
        """Legt den Ordnerpfad rekursiv an, falls er nicht existiert."""
        parts = [p for p in folder_path.strip("/").split("/") if p]
        current = ""
        for part in parts:
            current = f"{current}/{part}"
            url = self._url(current)
            resp = self.session.request("MKCOL", url, verify=self.verify_tls, timeout=30)
            if resp.status_code not in (201, 405):  # 405 = existiert schon
                resp.raise_for_status()

    def upload_file(self, local_path: str, remote_folder: str, remote_filename: str) -> None:
        self.ensure_folder(remote_folder)
        url = self._url(f"{remote_folder}/{remote_filename}")
        with open(local_path, "rb") as f:
            data = f.read()
        resp = self.session.put(url, data=data, verify=self.verify_tls, timeout=60)
        resp.raise_for_status()

    def upload_bytes(self, data: bytes, remote_folder: str, remote_filename: str) -> None:
        self.ensure_folder(remote_folder)
        url = self._url(f"{remote_folder}/{remote_filename}")
        resp = self.session.put(url, data=data, verify=self.verify_tls, timeout=60)
        resp.raise_for_status()