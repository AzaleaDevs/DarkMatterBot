import discord
from discord import app_commands
from discord.ext import commands
import sys
import os

# Add parent directory to sys.path to allow importing from hola_db
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered, register_user

class Start(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="start", description="Regístrate en el barrio y empieza a usar el bot.")
    async def start(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        user_name = interaction.user.name

        # Check if user is already registered
        is_registered = await is_user_registered(user_id)

        if is_registered:
            # User already exists
            await interaction.response.send_message(
                "Ya te han fichado en el barrio por lo que no hace falta registrarse de nuevo",
                ephemeral=True
            )
        else:
            # Register new user
            await register_user(user_id, user_name)
            
            # Create welcome embed
            embed = discord.Embed(
                title="¡Bienvenido al barrio!",
                description=f"Hola {user_name}, te acabas de registrar en el sistema.",
                color=discord.Color.green()
            )
            
            # Set user avatar in top right
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # Add important commands
            embed.add_field(
                name="📋 Comandos Importantes",
                value=(
                    "**`/inventario`** - Ver tu inventario de items y porros\n"
                    "**`/cali`** - Abrir un Cali Pack\n"
                    "**`/caja`** - Ver tu colección de porros por edición\n"
                    "**`/meme`** - Crear un meme personalizado\n"
                ),
                inline=False
            )
            
            embed.set_footer(text="¡Usa estos comandos para empezar tu aventura!")
            
            await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Start(bot))
