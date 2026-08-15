import discord
from discord import app_commands
from discord.ext import commands


class Pingy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pingy", description="Devuelve pongy con latencia.")
    async def pingy(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)  # Convertimos segundos → milisegundos
        
        embed = discord.Embed(
            title="🔊 Pongy!",
            description=f"Shard **{interaction.guild.shard_id}**: `{latency_ms}ms`",
            color=0xff5555  # Un color bonito similar al de la captura
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Pingy(bot))
