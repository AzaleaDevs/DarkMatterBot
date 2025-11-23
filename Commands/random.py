import discord
from discord import app_commands
from discord.ext import commands
import random

class Random(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="random", description="Genera un número aleatorio entre 1 y 100.")
    async def random_num(self, interaction: discord.Interaction):
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
