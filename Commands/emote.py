import discord
from discord import app_commands
from discord.ext import commands
from discord.interactions import Interaction
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered


class Emote(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(description="Devuelve pongy.")       
    async def emote(self, interaction: discord.Interaction):
        # Check if user is registered
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado en el barrio para poder usar estos comandos. Prueba a hacer /start",
                ephemeral=True
            )
            return
        
        # Returns discord emote with the discord developer portal ID emote
        await interaction.response.send_message(content = "<:rberry:1441940371146936410>")

async def setup(bot: commands.Bot):
    await bot.add_cog(Emote(bot))