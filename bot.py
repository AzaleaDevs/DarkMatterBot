import json
import os
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import aiosqlite
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

class DarkMatterBot(commands.Bot):
    def __init__(self, intents: discord.Intents):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            activity=discord.Game(name=config["STATE"])
        )
        self.db = None

    async def setup_hook(self):
        logger.info("Setting up the bot...")
        await self.load_extensions()
        await self.sync_commands()
        
        # -----------------------------
        #   INITIALIZACIÓN DE BD 
        #   (mantengo EXACTAMENTE lo tuyo)
        # -----------------------------
        # await self.connect_db()
        # logger.info("Database connected")
        # -----------------------------

        logger.info("BOT RUNNING")

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
