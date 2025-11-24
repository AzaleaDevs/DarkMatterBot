import discord
from discord import app_commands
from discord.ext import commands
import sys
import os

# Add parent directory to sys.path to allow importing from hola_db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import check_user, register_user

class Hola(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hola", description="Saluda y regístrate en la base de datos si eres nuevo.")
    async def hola(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_name = interaction.user.name

        existing_user = await check_user(user_id)

        if existing_user:
            await interaction.response.send_message(f"Hi, {user_name}")
        else:
            await register_user(user_id, user_name)
            await interaction.response.send_message(f"Hi {user_name}, I saved you in the database")

async def setup(bot: commands.Bot):
    await bot.add_cog(Hola(bot))
