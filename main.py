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
with open('config.json', encoding="utf8") as config_file:
    config = json.load(config_file)


# Config values
TOKEN = config["DISCORD_TOKEN"]
GUILD_ID = config["GUILD_ID"]
PREFIX = "!"
BOSS_KILL_API = config.get("BOSS_KILL_API", {})

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
        #   INITIALIZACIÓN DE BD 
        #   (mantengo EXACTAMENTE lo tuyo)
        # -----------------------------
        # await self.connect_db()
        # logger.info("Database connected")
        # -----------------------------

        logger.info("BOT RUNNING")

    async def start_boss_kill_api(self):
        if not BOSS_KILL_API.get("ENABLED", False):
            logger.info("Boss kill API disabled")
            return

        channel_id = BOSS_KILL_API.get("CHANNEL_ID")
        api_token = BOSS_KILL_API.get("TOKEN")
        if not channel_id or not api_token:
            logger.warning("Boss kill API requires BOSS_KILL_API.CHANNEL_ID and BOSS_KILL_API.TOKEN")
            return

        app = web.Application()
        app.add_routes([web.post("/azerothcore/boss-kill", self.handle_boss_kill)])

        host = BOSS_KILL_API.get("HOST", "0.0.0.0")
        port = int(BOSS_KILL_API.get("PORT", 8088))

        self.boss_kill_runner = web.AppRunner(app)
        await self.boss_kill_runner.setup()
        self.boss_kill_site = web.TCPSite(self.boss_kill_runner, host, port)
        await self.boss_kill_site.start()
        logger.info(f"Boss kill API listening on {host}:{port}")

    async def handle_boss_kill(self, request):
        expected_token = BOSS_KILL_API.get("TOKEN")
        request_token = request.headers.get("X-Darkmatter-Token")

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            request_token = auth_header.removeprefix("Bearer ").strip()

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
    #   Inicialización de base de datos (MANTENIDO TAL CUAL)
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
