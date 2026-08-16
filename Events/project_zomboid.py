import asyncio
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import posixpath
import stat
from typing import Any

import discord
from discord.ext import commands
import paramiko


logger = logging.getLogger(__name__)

with open("config.json", encoding="utf-8-sig") as config_file:
    PROJECT_ZOMBOID = json.load(config_file).get("PROJECT_ZOMBOID", {})


class ProjectZomboidBridge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = PROJECT_ZOMBOID
        self.enabled = bool(self.settings.get("ENABLED", False))
        self.state: dict[str, Any] | None = None
        self.last_sync: datetime | None = None
        self.last_error: str | None = None
        self._sync_lock = asyncio.Lock()
        self._cursor_path = Path("data") / "project_zomboid_cursor.json"
        self._known_hosts_path = Path("data") / "project_zomboid_known_hosts"
        self._event_offset = self._load_cursor()
        self._poll_task: asyncio.Task | None = None

        bot.project_zomboid_bridge = self
        if self.enabled:
            self._poll_task = asyncio.create_task(self._poll_loop())

    async def cog_unload(self):
        if self._poll_task:
            self._poll_task.cancel()

    def _load_cursor(self) -> int | None:
        try:
            data = json.loads(self._cursor_path.read_text(encoding="utf-8"))
            return max(0, int(data["offset"]))
        except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            return None

    def _save_cursor(self, offset: int) -> None:
        self._cursor_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self._cursor_path.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps({"offset": offset}, separators=(",", ":")),
            encoding="utf-8",
        )
        temp_path.replace(self._cursor_path)

    def _setting(self, name: str, env_name: str, default: Any = None) -> Any:
        return os.getenv(env_name) or self.settings.get(name, default)

    def _connect(self) -> tuple[paramiko.SSHClient, paramiko.SFTPClient]:
        host = self._setting("SFTP_HOST", "PZ_SFTP_HOST")
        port = int(self._setting("SFTP_PORT", "PZ_SFTP_PORT", 22))
        username = self._setting("SFTP_USERNAME", "PZ_SFTP_USERNAME")
        password = os.getenv("PZ_SFTP_PASSWORD")

        if not host or not username or not password:
            raise RuntimeError(
                "Faltan PZ_SFTP_HOST, PZ_SFTP_USERNAME o PZ_SFTP_PASSWORD"
            )

        self._known_hosts_path.parent.mkdir(parents=True, exist_ok=True)
        client = paramiko.SSHClient()
        if self._known_hosts_path.exists():
            client.load_host_keys(str(self._known_hosts_path))
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=str(host),
            port=port,
            username=str(username),
            password=password,
            look_for_keys=False,
            allow_agent=False,
            timeout=15,
            auth_timeout=15,
            banner_timeout=15,
        )
        client.save_host_keys(str(self._known_hosts_path))
        return client, client.open_sftp()

    @staticmethod
    def _read_json_file(sftp: paramiko.SFTPClient, remote_path: str) -> dict[str, Any]:
        with sftp.open(remote_path, "rb") as remote_file:
            raw = remote_file.read()
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("El estado de Project Zomboid no es un objeto JSON")
        return data

    @staticmethod
    def _read_text_file(sftp: paramiko.SFTPClient, remote_path: str) -> str:
        with sftp.open(remote_path, "rb") as remote_file:
            return remote_file.read().decode("utf-8-sig", errors="replace")

    @staticmethod
    def _parse_ini_list(content: str, setting_name: str) -> list[str]:
        expected = setting_name.casefold()
        for raw_line in content.splitlines():
            key, separator, value = raw_line.partition("=")
            if separator and key.strip().casefold() == expected:
                return [item.strip() for item in value.split(";") if item.strip()]
        return []

    @staticmethod
    def _find_mod_info_files(
        sftp: paramiko.SFTPClient,
        root: str,
        max_depth: int = 6,
    ) -> list[str]:
        found: list[str] = []
        pending = [(root, 0)]
        while pending:
            current_path, depth = pending.pop()
            try:
                entries = sftp.listdir_attr(current_path)
            except OSError:
                continue
            for entry in entries:
                child_path = posixpath.join(current_path, entry.filename)
                if stat.S_ISDIR(entry.st_mode) and depth < max_depth:
                    pending.append((child_path, depth + 1))
                elif entry.filename.casefold() == "mod.info":
                    found.append(child_path)
        return found

    def _fetch_installed_mods(self) -> list[str]:
        ini_path = str(self.settings.get("SERVER_INI_PATH", "")).strip()
        workshop_root = str(
            self.settings.get("WORKSHOP_CONTENT_PATH", "")
        ).strip()
        if not ini_path or not workshop_root:
            raise RuntimeError(
                "Faltan SERVER_INI_PATH o WORKSHOP_CONTENT_PATH en PROJECT_ZOMBOID"
            )

        client, sftp = self._connect()
        try:
            ini_content = self._read_text_file(sftp, ini_path)
            mod_ids = self._parse_ini_list(ini_content, "Mods")
            workshop_ids = self._parse_ini_list(ini_content, "WorkshopItems")

            names_by_id: dict[str, str] = {}
            discovered_names: list[str] = []
            for workshop_id in workshop_ids:
                item_root = posixpath.join(workshop_root, workshop_id)
                for info_path in self._find_mod_info_files(sftp, item_root):
                    metadata: dict[str, str] = {}
                    for raw_line in self._read_text_file(sftp, info_path).splitlines():
                        key, separator, value = raw_line.partition("=")
                        if separator:
                            metadata[key.strip().casefold()] = value.strip()
                    mod_id = metadata.get("id")
                    mod_name = metadata.get("name")
                    if mod_name and mod_name not in discovered_names:
                        discovered_names.append(mod_name)
                    if mod_id and mod_name:
                        names_by_id.setdefault(mod_id, mod_name)

            if mod_ids:
                return [names_by_id.get(mod_id, mod_id) for mod_id in mod_ids]
            return discovered_names
        finally:
            sftp.close()
            client.close()

    async def get_installed_mods(self) -> list[str]:
        if not self.enabled:
            raise RuntimeError("La integracion de Project Zomboid esta desactivada")
        return await asyncio.to_thread(self._fetch_installed_mods)

    def _read_events(
        self,
        sftp: paramiko.SFTPClient,
        remote_path: str,
    ) -> tuple[list[dict[str, Any]], int]:
        try:
            size = int(sftp.stat(remote_path).st_size)
        except OSError as exc:
            if exc.errno == 2:
                return [], 0
            raise

        if self._event_offset is None:
            return [], size

        offset = self._event_offset if size >= self._event_offset else 0
        if size == offset:
            return [], offset

        with sftp.open(remote_path, "rb") as remote_file:
            remote_file.seek(offset)
            payload = remote_file.read()

        event_prefix = str(self.settings.get("EVENT_PREFIX", "")).encode("utf-8")

        events: list[dict[str, Any]] = []
        consumed = 0
        for raw_line in payload.splitlines(keepends=True):
            if not raw_line.endswith((b"\n", b"\r")):
                break
            consumed += len(raw_line)
            line = raw_line.strip()
            if not line:
                continue
            if event_prefix:
                prefix_index = line.find(event_prefix)
                if prefix_index < 0:
                    continue
                line = line[prefix_index + len(event_prefix):].strip()
            try:
                event = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                logger.warning("Ignoring malformed Project Zomboid event line")
                continue
            if isinstance(event, dict):
                events.append(event)

        return events, offset + consumed

    def _fetch_remote(self) -> tuple[dict[str, Any], list[dict[str, Any]], int]:
        state_path = str(self.settings.get("STATE_PATH", "")).strip()
        events_path = str(self.settings.get("EVENTS_PATH", "")).strip()
        if not state_path or not events_path:
            raise RuntimeError("Faltan STATE_PATH o EVENTS_PATH en PROJECT_ZOMBOID")

        client, sftp = self._connect()
        try:
            state = self._read_json_file(sftp, state_path)
            events, next_offset = self._read_events(sftp, events_path)
            return state, events, next_offset
        finally:
            sftp.close()
            client.close()

    async def sync(self) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("La integracion de Project Zomboid esta desactivada")

        async with self._sync_lock:
            try:
                state, events, next_offset = await asyncio.to_thread(self._fetch_remote)
                self.state = state
                self.last_sync = datetime.now(timezone.utc)
                self.last_error = None

                for event in events:
                    if event.get("type") == "player_death":
                        await self._send_death_notification(event)

                self._event_offset = next_offset
                await asyncio.to_thread(self._save_cursor, next_offset)
                return state
            except Exception as exc:
                self.last_error = str(exc)
                raise

    async def _send_death_notification(self, event: dict[str, Any]) -> None:
        channel_id = self.settings.get("CHANNEL_ID")
        if not channel_id:
            raise RuntimeError("Falta PROJECT_ZOMBOID.CHANNEL_ID")

        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            channel = await self.bot.fetch_channel(int(channel_id))

        display_name = (
            event.get("display_name")
            or event.get("username")
            or "Superviviente desconocido"
        )
        embed = discord.Embed(
            title="Superviviente caido",
            description=f"**{display_name}** ha muerto en Project Zomboid.",
            color=discord.Color.dark_red(),
        )

        hours = float(event.get("hours_survived") or 0)
        kills = int(event.get("zombie_kills") or 0)
        embed.add_field(name="Supervivencia", value=f"{hours:.1f} horas", inline=True)
        embed.add_field(name="Zombis abatidos", value=str(kills), inline=True)

        game = event.get("game") or {}
        if game:
            embed.add_field(
                name="Hora ingame",
                value=self.format_game_time(game),
                inline=False,
            )

        if all(key in event for key in ("x", "y", "z")):
            embed.add_field(
                name="Coordenadas",
                value=f"{event['x']}, {event['y']}, {event['z']}",
                inline=False,
            )

        embed.set_footer(text=str(self.settings.get("SERVER_NAME", "Project Zomboid")))

        thumbnail_file = None
        thumbnail_path = Path("Images") / "avatar.png"
        if thumbnail_path.is_file():
            thumbnail_file = discord.File(thumbnail_path, filename="avatar.png")
            embed.set_thumbnail(url="attachment://avatar.png")

        if thumbnail_file:
            await channel.send(embed=embed, file=thumbnail_file)
        else:
            await channel.send(embed=embed)

    @staticmethod
    def format_game_time(game: dict[str, Any]) -> str:
        day = int(game.get("day", 1))
        month = int(game.get("month", 1))
        year = int(game.get("year", 1993))
        hour = int(game.get("hour", 0))
        minute = int(game.get("minute", 0))
        return f"{day:02d}/{month:02d}/{year} - {hour:02d}:{minute:02d}"

    async def _poll_loop(self) -> None:
        await self.bot.wait_until_ready()
        interval = max(10, int(self.settings.get("POLL_SECONDS", 30)))

        while not self.bot.is_closed():
            try:
                await self.sync()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Project Zomboid SFTP sync failed")

            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break


async def setup(bot: commands.Bot):
    await bot.add_cog(ProjectZomboidBridge(bot))
