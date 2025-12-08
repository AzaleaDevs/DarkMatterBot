import discord
from discord import app_commands
from discord.ext import commands
import random
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered

class Random(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="random", description="Genera un número aleatorio entre 1 y 100.")
    async def random_num(self, interaction: discord.Interaction):
        # Check if user is registered
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado en el barrio para poder usar estos comandos. Prueba a hacer /start",
                ephemeral=True
            )
            return
        
        number = random.randint(1, 100)
        
        embed = discord.Embed(
            description=f"🎲 El número es: **{number}**",
            color=0x800080 # Purple
        )
        
        if interaction.user.avatar:
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        else:
            embed.set_author(name=interaction.user.name, icon_url=interaction.user.default_avatar.url)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Random(bot))
