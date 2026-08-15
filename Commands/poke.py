import discord
from discord import app_commands
from discord.ext import commands
import os
import random

class Poke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Absolute path to the Pokes directory
        self.pokes_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Pokes'))

    @app_commands.command(name="poke", description="Muestra un pokemon aleatorio de la carpeta Pokes.")
    async def poke(self, interaction: discord.Interaction):
        if not os.path.exists(self.pokes_path):
            await interaction.response.send_message("Lo siento, no encuentro la carpeta de Pokes.", ephemeral=True)
            return

        # List all files in the Pokes directory
        try:
            files = [f for f in os.listdir(self.pokes_path) if os.path.isfile(os.path.join(self.pokes_path, f))]
        except Exception as e:
            await interaction.response.send_message(f"Error al leer la carpeta: {e}", ephemeral=True)
            return

        if not files:
            await interaction.response.send_message("La carpeta de Pokes está vacía.", ephemeral=True)
            return

        # Select a random file
        random_file = random.choice(files)
        file_path = os.path.join(self.pokes_path, random_file)

        # Create the embed
        embed = discord.Embed(
            description="Este es tu poke aleatorio!",
            color=discord.Color.random()
        )
        
        # Create discord File object
        file = discord.File(file_path, filename=random_file)
        embed.set_image(url=f"attachment://{random_file}")

        await interaction.response.send_message(embed=embed, file=file)

async def setup(bot: commands.Bot):
    await bot.add_cog(Poke(bot))
