import discord
from discord import app_commands
from discord.ext import commands
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered

class Prueba(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="prueba", description="Comando de prueba.")
    async def prueba(self, interaction: discord.Interaction):
        # Check if user is registered
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado en el barrio para poder usar estos comandos. Prueba a hacer /start",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message(f"Prueba {interaction.user.mention}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Prueba(bot))
