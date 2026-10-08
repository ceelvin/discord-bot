# Nickname-Bot

Zeigt den Status „Spielt World of Warcraft Forever“ mit Zone, Gruppe und Spielzeit als Text. Ein Bild kann ein Bot nicht setzen. Setzt Server-Nicknames anhand von Rollen. Das Emoji der höchsten passenden Rolle hängt hinten am bestehenden Namen. Alte eigene Suffixe und die früheren Text-Prefixe `[TANK] `, `[HEAL] `, `[DPS] ` werden vorher entfernt, der Rest bleibt. Ohne passende Rolle wird das Suffix entfernt. Nicknames werden auf 32 Zeichen gekürzt. Server-Owner und Bots werden nicht angefasst.

## Discord einrichten

1. Im [Discord Developer Portal](https://discord.com/developers/applications) eine Application anlegen.
2. Unter **Bot** einen Bot anlegen und den Token kopieren. Token nur in `.env` als `DISCORD_TOKEN` eintragen, nie in den Code.
3. Unter **Bot → Privileged Gateway Intents** den **Server Members Intent** einschalten.
4. Bot einladen mit Scope `bot` und der Berechtigung **Manage Nicknames**:

   `https://discord.com/api/oauth2/authorize?client_id=DEINE_CLIENT_ID&permissions=134217728&scope=bot`

   `DEINE_CLIENT_ID` ist die Application ID.

5. Die Bot-Rolle in der Rollenliste über die Mitglieder ziehen, die umbenannt werden sollen. Mitglieder mit einer höheren Rolle kann der Bot nicht umbenennen. Den Server-Owner kann der Bot nicht umbenennen.
6. Entwicklermodus einschalten (Benutzereinstellungen → Erweitert). Rechtsklick auf die Rolle → ID kopieren. IDs und Emoji-Suffixe in `config.json` eintragen. Vorlage: `config.example.json`.

Gewonnen hat die höchste passende Rolle in der Discord-Rollenliste, nicht die Reihenfolge in `config.json`. Ein manuell geänderter Nickname ohne oder mit falschem Suffix wird wieder gesetzt. Fehlende Rechte werden geloggt, der Bot läuft weiter.

## Auf dem VPS

Ein Container, kein offener Port. Der Bot hört auf nichts und verbindet sich nur ausgehend mit Discord. Er läuft neben anderen Diensten.

```bash
cp .env.example .env
```

Token in `.env` eintragen, ohne Anführungszeichen. Rollen-IDs in `config.json` eintragen, dann:

```bash
docker compose up -d --build
docker compose logs -f
```

`config.json` liegt im Image. Nach Änderungen daran erneut `docker compose up -d --build`.
