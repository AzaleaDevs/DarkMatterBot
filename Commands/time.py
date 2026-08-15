import discord
from discord import app_commands
from discord.ext import commands


class ProjectZomboidTime(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="time",
        description="Muestra la fecha y hora actual del servidor de Project Zomboid.",
    )
    async def time(self, interaction: discord.Interaction):
        bridge = getattr(self.bot, "project_zomboid_bridge", None)
        if bridge is None or not bridge.enabled:
            await interaction.response.send_message(
                "La integracion de Project Zomboid no esta configurada.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True)

        try:
            state = await bridge.sync()
        except Exception:
            if bridge.state is None:
                await interaction.followup.send(
                    "No se pudo consultar el servidor de Project Zomboid.",
                    ephemeral=True,
                )
                return
            state = bridge.state

        game = state.get("game") or {}
        embed = discord.Embed(
            title=bridge.settings.get("SERVER_NAME", "Project Zomboid"),
            description=f"**{bridge.format_game_time(game)}**",
            color=discord.Color.dark_green(),
        )
        embed.add_field(
            name="Dia del mundo",
            value=str(int(game.get("days_survived", 0)) + 1),
            inline=True,
        )
        embed.add_field(
            name="Jugadores conectados",
            value=str(int(state.get("players_online", 0))),
            inline=True,
        )

        if bridge.last_sync:
            embed.timestamp = bridge.last_sync
            embed.set_footer(text="Ultima sincronizacion")

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProjectZomboidTime(bot))
