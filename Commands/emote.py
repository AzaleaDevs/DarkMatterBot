import discord
from discord import app_commands
from discord.ext import commands
from discord.interactions import Interaction



class Emote(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(description="Devuelve pongy.")       
    async def emote(self, interaction: discord.Interaction):
        # Returns discord emote with the discord developer portal ID emote
        await interaction.response.send_message(content = "<:rberry:1441940371146936410>")

async def setup(bot: commands.Bot):
    await bot.add_cog(Emote(bot))