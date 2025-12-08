import discord
from discord import app_commands
from discord.ext import commands
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered

class Pingy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pingy", description="Devuelve pongy con latencia.")
    async def pingy(self, interaction: discord.Interaction):
        # Check if user is registered
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado en el barrio para poder usar estos comandos. Prueba a hacer /start",
                ephemeral=True
            )
            return
        
        latency_ms = round(self.bot.latency * 1000)  # Convertimos segundos → milisegundos
        
        embed = discord.Embed(
            title="🔊 Pongy!",
            description=f"Shard **{interaction.guild.shard_id}**: `{latency_ms}ms`",
            color=0xff5555  # Un color bonito similar al de la captura
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Pingy(bot))
