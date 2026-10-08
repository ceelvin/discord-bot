import json
import logging
import os
import sys
import time
import unicodedata
from pathlib import Path

import discord

log = logging.getLogger("nickname-bot")

NICK_LIMIT = 32
CONFIG_PATH = Path(__file__).with_name("config.json")
PLAYING_SINCE = time.time()


def playing_activity() -> discord.Activity:
    return discord.Activity(
        type=discord.ActivityType.playing,
        name="World of Warcraft Forever",
        details="Elwynnwald",
        state="Solo",
        timestamps={"start": int(PLAYING_SINCE * 1000)},
        assets={
            "large_text": "World of Warcraft Forever",
            "small_text": "Krieger - Stufe 60",
        },
        party={"id": "lidl-lootlords", "size": [1, 5]},
    )


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


LEGACY_PREFIXES = ("[TANK] ", "[HEAL] ", "[DPS] ")
LEGACY_EMOJIS = ("💚",)


def load_config(path: Path) -> tuple[dict[int, str], list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        log.error("config.json fehlt")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        log.error("config.json ist kein gültiges JSON: %s", exc)
        sys.exit(1)

    entries = data.get("roles")
    if not isinstance(entries, list) or not entries:
        log.error("config.json: 'roles' muss eine nicht-leere Liste sein")
        sys.exit(1)

    role_suffixes: dict[int, str] = {}
    suffixes: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            log.error("config.json: jeder Eintrag braucht 'id' und 'suffix'")
            sys.exit(1)
        try:
            role_id = int(entry["id"])
            suffix = entry["suffix"]
        except (KeyError, TypeError, ValueError):
            log.error("config.json: jeder Eintrag braucht 'id' und 'suffix'")
            sys.exit(1)
        if not isinstance(suffix, str) or role_id <= 0 or suffix == "" or suffix.strip() == "":
            log.error("config.json: ungültige Rollen-ID oder leeres Suffix")
            sys.exit(1)
        if len(suffix) >= NICK_LIMIT:
            log.error("config.json: Suffix für Rolle %s ist zu lang", role_id)
            sys.exit(1)
        role_suffixes[role_id] = suffix
        if suffix not in suffixes:
            suffixes.append(suffix)

    suffixes.sort(key=len, reverse=True)
    return role_suffixes, suffixes


def normalize(name: str) -> str:
    return unicodedata.normalize("NFC", name).replace("\ufe0f", "").replace("\ufe0e", "")


def discord_len(name: str) -> int:
    return len(name.encode("utf-16-le")) // 2


def trim_discord(name: str, limit: int = NICK_LIMIT) -> str:
    units = 0
    out: list[str] = []
    for char in name:
        size = discord_len(char)
        if units + size > limit:
            break
        out.append(char)
        units += size
    return "".join(out).rstrip()


def strip_markers(name: str, suffixes: list[str]) -> str:
    markers = [normalize(suffix.strip()) for suffix in suffixes if suffix.strip()]
    for emoji in LEGACY_EMOJIS:
        marker = normalize(emoji)
        if marker not in markers:
            markers.append(marker)
    markers.sort(key=len, reverse=True)
    prefixes = sorted((normalize(prefix) for prefix in LEGACY_PREFIXES), key=len, reverse=True)
    changed = True
    while changed:
        changed = False
        name = normalize(name)
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix) :]
                changed = True
                break
        if changed:
            continue
        stripped = name.rstrip()
        for marker in markers:
            if stripped.endswith(marker):
                name = stripped[: -len(marker)].rstrip()
                changed = True
                break
    return name.rstrip()


def matching_suffix(member: discord.Member, role_suffixes: dict[int, str]) -> str | None:
    best_pos = -1
    best: str | None = None
    for role in member.roles:
        suffix = role_suffixes.get(role.id)
        if suffix is not None and role.position > best_pos:
            best = suffix
            best_pos = role.position
    return best


def desired_nick(member: discord.Member, suffix: str | None, suffixes: list[str]) -> str | None:
    if member.nick is None and suffix is None:
        return None
    raw = member.nick if member.nick is not None else member.display_name
    base = strip_markers(raw, suffixes).strip()
    if base == "":
        base = member.name
    if suffix is None:
        return trim_discord(base)
    room = NICK_LIMIT - discord_len(suffix)
    if room < 1:
        return trim_discord(suffix)
    return f"{trim_discord(base, room)}{suffix}"


class NicknameBot(discord.Client):
    def __init__(self, role_suffixes: dict[int, str], suffixes: list[str]) -> None:
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents, activity=playing_activity())
        self.role_suffixes = role_suffixes
        self.suffixes = suffixes
        self._startup_done = False

    async def on_ready(self) -> None:
        log.info("Eingeloggt als %s", self.user)
        try:
            await self.change_presence(activity=playing_activity())
        except discord.HTTPException as exc:
            log.warning("Status nicht gesetzt: %s", exc)
        if self._startup_done:
            return
        self._startup_done = True
        for guild in self.guilds:
            log.info("Prüfe Mitglieder in %s", guild.name)
            try:
                async for member in guild.fetch_members(limit=None):
                    await self.apply_nickname(member)
            except discord.Forbidden:
                log.warning("Keine Berechtigung, Mitglieder in %s zu laden", guild.name)
            except discord.HTTPException as exc:
                log.warning("Mitglieder in %s konnten nicht geladen werden: %s", guild.name, exc)

    async def on_member_join(self, member: discord.Member) -> None:
        await self.apply_nickname(member)

    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if before.roles == after.roles and before.nick == after.nick:
            return
        await self.apply_nickname(after)

    async def apply_nickname(self, member: discord.Member) -> None:
        if member.bot or member.id == member.guild.owner_id:
            return
        suffix = matching_suffix(member, self.role_suffixes)
        desired = desired_nick(member, suffix, self.suffixes)
        if member.nick == desired:
            return
        try:
            await member.edit(nick=desired, reason="Rollen-Suffix")
            log.info("Nickname %s: %r -> %r", member, member.nick, desired)
        except discord.Forbidden:
            log.warning("Keine Berechtigung, Nickname von %s (%s) zu ändern", member, member.id)
        except discord.HTTPException as exc:
            log.warning("Nickname von %s nicht geändert: %s", member, exc)


def main() -> None:
    setup_logging()
    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token:
        log.error("Umgebungsvariable DISCORD_TOKEN fehlt")
        sys.exit(1)
    role_suffixes, suffixes = load_config(CONFIG_PATH)
    NicknameBot(role_suffixes, suffixes).run(token, log_handler=None)


if __name__ == "__main__":
    main()
