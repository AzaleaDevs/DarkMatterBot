import discord
from discord import app_commands
from discord.ext import commands

class Prueba(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="prueba", description="Comando de prueba.")
    async def prueba(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Prueba {interaction.user.mention}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Prueba(bot))
