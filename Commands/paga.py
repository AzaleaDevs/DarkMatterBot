import discord
from discord import app_commands
from discord.ext import commands
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered
from db_utils import update_user_currency, get_last_paga, update_last_paga

class Paga(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="paga", description="Recibe tu paga de 10€ cada hora.")
    async def paga(self, interaction: discord.Interaction):
        # 1. Check registration
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado en el barrio. Usa /start para empezar.",
                ephemeral=True
            )
            return

        # 2. Check cooldown
        last_paga_str = await get_last_paga(interaction.user.id)
        now = datetime.utcnow()
        
        if last_paga_str:
            last_paga = datetime.fromisoformat(last_paga_str)
            # Check if 1 hour has passed
            if now < last_paga + timedelta(hours=1):
                remaining = (last_paga + timedelta(hours=1)) - now
                minutes = int(remaining.total_seconds() // 60)
                await interaction.response.send_message(
                    f"Tienes que esperar {minutes} minutos antes de recibir una nueva paga.",
                    ephemeral=True
                )
                return

        # 3. Give money
        await update_user_currency(interaction.user.id, euros=10)
        
        # 4. Update timestamp
        await update_last_paga(interaction.user.id, now.isoformat())

        # 5. Respond
        embed = discord.Embed(
            title="💶 Paga Recibida",
            description=f"Has recibido tus **10€** diarios (bueno, horarios). \n¡Gástalos con sabiduría!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Paga(bot))
