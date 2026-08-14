import json
import os
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import aiosqlite
from aiohttp import web
from os import listdir
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load config
with open('config.json', encoding="utf-8-sig") as config_file:
    config = json.load(config_file)


# Config values
TOKEN = os.getenv("DISCORD_TOKEN") or config.get("DISCORD_TOKEN")
GUILD_ID = config["GUILD_ID"]
PREFIX = "!"
BOSS_KILL_API = config.get("BOSS_KILL_API", {})
MINECRAFT_API = config.get("MINECRAFT_API", {})

if not TOKEN or TOKEN.startswith("<"):
    raise RuntimeError("Missing DISCORD_TOKEN. Set it in .env or as an environment variable.")

class DarkMatterBot(commands.Bot):
    def __init__(self, intents: discord.Intents):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            activity=discord.Game(name=config["STATE"])
        )
        self.db = None
        self.boss_kill_runner = None
        self.boss_kill_site = None

    async def setup_hook(self):
        logger.info("Setting up the bot...")
        await self.load_extensions()
        await self.sync_commands()
        await self.start_boss_kill_api()
        
        # -----------------------------
        #   INITIALIZACIÃ“N DE BD 
        #   (mantengo EXACTAMENTE lo tuyo)
        # -----------------------------
        # await self.connect_db()
        # logger.info("Database connected")
        # -----------------------------

        logger.info("BOT RUNNING")

    async def start_boss_kill_api(self):
        boss_api_enabled = BOSS_KILL_API.get("ENABLED", False)
        minecraft_api_enabled = MINECRAFT_API.get("ENABLED", False)
        if not boss_api_enabled and not minecraft_api_enabled:
            logger.info("Game event API disabled")
            return

        if boss_api_enabled and (not BOSS_KILL_API.get("CHANNEL_ID") or not BOSS_KILL_API.get("TOKEN")):
            logger.warning("Boss kill API requires BOSS_KILL_API.CHANNEL_ID and BOSS_KILL_API.TOKEN")
            return

        if minecraft_api_enabled and (not MINECRAFT_API.get("CHANNEL_ID") or not MINECRAFT_API.get("TOKEN")):
            logger.warning("Minecraft API requires MINECRAFT_API.CHANNEL_ID and MINECRAFT_API.TOKEN")
            return

        app = web.Application()
        app.add_routes([web.post("/azerothcore/boss-kill", self.handle_boss_kill)])
        app.add_routes([web.post("/minecraft/player-join", self.handle_minecraft_player_join)])

        server_config = MINECRAFT_API if minecraft_api_enabled else BOSS_KILL_API
        host = server_config.get("HOST", BOSS_KILL_API.get("HOST", "0.0.0.0"))
        port = int(server_config.get("PORT", BOSS_KILL_API.get("PORT", 8088)))

        self.boss_kill_runner = web.AppRunner(app)
        await self.boss_kill_runner.setup()
        self.boss_kill_site = web.TCPSite(self.boss_kill_runner, host, port)
        await self.boss_kill_site.start()
        logger.info(f"Game event API listening on {host}:{port}")

    def get_request_token(self, request):
        request_token = request.headers.get("X-Darkmatter-Token")

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            request_token = auth_header.removeprefix("Bearer ").strip()

        return request_token

    async def handle_boss_kill(self, request):
        expected_token = BOSS_KILL_API.get("TOKEN")
        request_token = self.get_request_token(request)

        if request_token != expected_token:
            return web.json_response({"error": "unauthorized"}, status=401)

        try:
            payload = await request.json()
        except ValueError:
            return web.json_response({"error": "invalid json"}, status=400)

        boss_name = str(payload.get("boss_name") or "Boss desconocido")
        killer_name = str(payload.get("killer_name") or "jugadores desconocidos")
        boss_entry = payload.get("boss_entry")
        zone = payload.get("zone")
        map_name = payload.get("map")
        difficulty = payload.get("difficulty")

        embed = discord.Embed(
            title="Boss derrotado",
            description=f"**{boss_name}** ha sido derrotado por **{killer_name}**.",
            color=discord.Color.dark_gold()
        )
        thumbnail_file = None
        thumbnail_path = os.path.join("Images", "avatar.png")
        if os.path.isfile(thumbnail_path):
            thumbnail_file = discord.File(thumbnail_path, filename="avatar.png")
            embed.set_thumbnail(url="attachment://avatar.png")

        if boss_entry:
            embed.add_field(name="Entry", value=str(boss_entry), inline=True)
        if zone:
            embed.add_field(name="Zona", value=str(zone), inline=True)
        if map_name:
            embed.add_field(name="Mapa", value=str(map_name), inline=True)
        if difficulty:
            embed.add_field(name="Dificultad", value=str(difficulty), inline=True)

        channel = self.get_channel(int(BOSS_KILL_API["CHANNEL_ID"]))
        if channel is None:
            channel = await self.fetch_channel(int(BOSS_KILL_API["CHANNEL_ID"]))

        if thumbnail_file:
            await channel.send(embed=embed, file=thumbnail_file)
        else:
            await channel.send(embed=embed)
        logger.info(f"Boss kill notification sent: {boss_name} by {killer_name}")
        return web.json_response({"ok": True})

    async def handle_minecraft_player_join(self, request):
        expected_token = MINECRAFT_API.get("TOKEN")
        request_token = self.get_request_token(request)

        if request_token != expected_token:
            return web.json_response({"error": "unauthorized"}, status=401)

        try:
            payload = await request.json()
        except ValueError:
            return web.json_response({"error": "invalid json"}, status=400)

        player_name = str(payload.get("player_name") or "Jugador desconocido")
        player_uuid = str(payload.get("player_uuid") or "").replace("-", "")
        server_name = str(payload.get("server_name") or MINECRAFT_API.get("SERVER_NAME") or "Minecraft")

        embed = discord.Embed(
            title="Jugador conectado",
            description=f"**{player_name}** se ha conectado.",
            color=discord.Color.green()
        )
        embed.add_field(name="Servidor", value=server_name, inline=True)

        if MINECRAFT_API.get("USE_SKIN_THUMBNAIL", True) and player_uuid:
            embed.set_thumbnail(url=f"https://crafatar.com/avatars/{player_uuid}?size=128&overlay")

        channel = self.get_channel(int(MINECRAFT_API["CHANNEL_ID"]))
        if channel is None:
            channel = await self.fetch_channel(int(MINECRAFT_API["CHANNEL_ID"]))

        await channel.send(embed=embed)
        logger.info(f"Minecraft join notification sent: {player_name} on {server_name}")
        return web.json_response({"ok": True})

    async def close(self):
        if self.boss_kill_runner:
            await self.boss_kill_runner.cleanup()
        await super().close()

    async def load_extensions(self):
        # Load commands from Commands/
        for command in [
            f"Commands.{file[:-3]}" for file in listdir('Commands') if file.endswith('.py')
        ]:
            await self.load_extension(command)
            logger.info(f"Loaded command extension: {command}")

        # Load events from Events/ (si existen)
        if os.path.isdir("Events"):
            for event in [
                f"Events.{file[:-3]}" for file in listdir('Events') if file.endswith('.py')
            ]:
                await self.load_extension(event)
                logger.info(f"Loaded event extension: {event}")

    async def sync_commands(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        logger.info("Commands synced")

    # -----------------------------------------------------------
    #   InicializaciÃ³n de base de datos (MANTENIDO TAL CUAL)
    # -----------------------------------------------------------
    # async def connect_db(self):
    #     self.db = await aiosqlite.connect(r"Files/memeria.db")
    #     self.db.row_factory = aiosqlite.Row
    #     logger.info("Database connected")
    # -----------------------------------------------------------


intents = discord.Intents.default()
intents.message_content = True

bot = DarkMatterBot(intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logger.info('------')

bot.run(TOKEN)


