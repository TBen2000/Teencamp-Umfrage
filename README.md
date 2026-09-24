# TeenCamp-Terminumfrage – Auswertung

Dieses Programm lädt die Ergebnisse **einer ganz bestimmten Nextcloud-Forms-Umfrage**
(zur Terminplanung eines Teencamps) herunter, erstellt daraus mehrere Diagramme
sowie einen Markdown-Bericht mit allen Anmerkungen, und lädt die Ergebnisse
anschließend wieder in einen Nextcloud-Ordner hoch.

> ⚠️ **Wichtig:** Dieses Skript ist speziell auf die Fragen der TeenCamp-Umfrage
> zugeschnitten (siehe unten). Es ist **kein allgemeines Nextcloud-Forms-Tool**
> und kann nicht ohne Anpassung für andere Formulare verwendet werden.

## Erwartete Fragen in der Umfrage

1. „Ich bin:“ – Teen / Mitarbeiter / Elternteil / Andere (mit Freitext)
2. „Ich / mein Kind war auf folgenden Teencamps dabei:“ – Mehrfachauswahl
   (2026, 2025, 2024, Auf keinem der drei)
3. „Dass das Teencamp in der vierten Woche der Sommerferien stattfindet,
   ist für mich geschickt.“ – Skala 1–5
4. „Wenn das Teencamp fünf Tage später anfangen würde, wäre das für mich
   geschickt.“ – Skala 1–5
5. „Ich wäre auf jeden Fall auf dem Teencamp dabei, unabhängig davon, wie
   geschickt oder ungeschickt es für mich liegt.“ – Skala 1–5
6. „Ich würde mir MEHR als sieben Tage Teencamp wünschen.“ – Skala 1–5
7. „Ich würde mir WENIGER als sieben Tage Teencamp wünschen.“ – Skala 1–5
8. „Weitere Anmerkungen sämtlicher Art:“ – Freitext (optional)

Die Fragen werden über Teilwort-Erkennung im Fragetext gefunden, sodass
kleinere Formulierungsänderungen kein Problem sind. Werden Formulierungen
stark verändert, bricht das Programm mit einer klaren Fehlermeldung ab.

## Funktionsweise

- Alle **15 Minuten** (änderbar) wird geprüft, ob sich die Umfrageergebnisse
  geändert haben (neue, geänderte oder gelöschte Antworten).
- **Bei Änderungen** werden alle Diagramme und der Markdown-Bericht neu
  erstellt und in den Ziel-Ordner hoch

## Umgebungsvariablen

| Variable            | Pflicht? | Standardwert              | Beschreibung |
|----------------------|----------|----------------------------|---------------|
| `NC_URL`             | ✅ Ja    | –                          | Basis-URL deiner Nextcloud-Instanz, z. B. `https://cloud.example.com` (ohne abschließenden Slash). |
| `NC_USER`            | ✅ Ja    | –                          | Nextcloud-Benutzername. Dieser Account muss **Besitzer** der Umfrage sein. |
| `NC_PASSWORD`        | ✅ Ja*   | –                          | Passwort des Nextcloud-Accounts (dein normales Login-Passwort, kein App-Passwort nötig). |
| `NC_PASSWORD_FILE`   | ✅ Ja*   | –                          | Alternative zu `NC_PASSWORD`: Pfad zu einer Datei, die das Passwort enthält (z. B. für Docker Secrets). Wird nur verwendet, wenn `NC_PASSWORD` nicht gesetzt ist. |
| `NC_FORM_LINK`       | ✅ Ja**  | –                          | Freigabe-Link der Umfrage, z. B. `https://cloud.example.com/index.php/apps/forms/s/AbCdEfGh`. Wird **primär** zur Identifikation des Formulars genutzt. |
| `NC_FORM_NAME`       | ✅ Ja**  | –                          | Titel der Umfrage (Teilwort-Matching möglich). Wird nur als **Fallback** verwendet, falls `NC_FORM_LINK` fehlt oder nicht gefunden wird. |
| `NC_TARGET_FOLDER`   | ❌ Nein  | `/TeenCamp-Auswertung`     | Nextcloud-Zielordner (WebDAV-Pfad), in den Diagramme, der Markdown-Bericht und `Last_Updated.txt` hochgeladen werden. Wird automatisch angelegt, falls er (oder Teile des Pfads) noch nicht existiert. |
| `INTERVAL_MINUTES`   | ❌ Nein  | `15`                       | Intervall in Minuten, in dem geprüft wird, ob sich die Umfragedaten geändert haben. |
| `VERIFY_TLS`         | ❌ Nein  | `true`                     | Auf `false` setzen, um TLS-Zertifikatsprüfung zu deaktivieren (z. B. bei selbstsignierten Zertifikaten). Für den normalen Betrieb nicht nötig. |

\* Es muss entweder `NC_PASSWORD` **oder** `NC_PASSWORD_FILE` gesetzt sein.  
\** Es muss mindestens `NC_FORM_LINK` **oder** `NC_FORM_NAME` gesetzt sein. Sind beide gesetzt, hat `NC_FORM_LINK` Vorrang; nur wenn darüber keine Übereinstimmung gefunden wird, wird auf `NC_FORM_NAME` zurückgegriffen.

### Beispiel: `docker run`

```bash
docker run -d \
  --name teencamp-auswertung \
  -e NC_URL="https://cloud.example.com" \
  -e NC_USER="mein.benutzername" \
  -e NC_PASSWORD="mein-geheimes-passwort" \
  -e NC_FORM_LINK="https://cloud.example.com/index.php/apps/forms/s/AbCdEfGh" \
  -e NC_TARGET_FOLDER="/TeenCamp/Umfrage-2026/Auswertung" \
  -e INTERVAL_MINUTES="15" \
  ghcr.io/dein-user/dein-repo:latest