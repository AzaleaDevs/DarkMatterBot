from pathlib import Path
import logging

import aiosqlite
import discord
from discord import app_commands
from discord.ext import commands


DB_PATH = Path("Databases") / "darkmatter_pro.db"
logger = logging.getLogger(__name__)


async def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS SUGERENCIAS (
                id_sugerencia INTEGER PRIMARY KEY AUTOINCREMENT,
                texto_sugerencia TEXT NOT NULL CHECK(length(texto_sugerencia) <= 240)
            )
            """
        )
        await db.commit()


class ConfirmDeleteView(discord.ui.View):
    def __init__(self, requester_id: int, suggestion_id: int):
        super().__init__(timeout=60)
        self.requester_id = requester_id
        self.suggestion_id = suggestion_id
        self.message: discord.InteractionMessage | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.requester_id:
            return True
        await interaction.response.send_message(
            "Solo quien inició el borrado puede responder a esta confirmación.",
            ephemeral=True,
        )
        return False

    def disable_buttons(self) -> None:
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="Sí", style=discord.ButtonStyle.success)
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "DELETE FROM SUGERENCIAS WHERE id_sugerencia = ?",
                (self.suggestion_id,),
            )
            await db.commit()

        self.disable_buttons()
        if cursor.rowcount:
            message = f"Sugerencia #{self.suggestion_id} eliminada."
        else:
            message = f"La sugerencia #{self.suggestion_id} ya no existe."
        await interaction.response.edit_message(content=message, embed=None, view=self)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.danger)
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        self.disable_buttons()
        await interaction.response.edit_message(
            content="Borrado cancelado.",
            embed=None,
            view=self,
        )
        self.stop()

    async def on_timeout(self) -> None:
        self.disable_buttons()
        if self.message:
            try:
                await self.message.edit(content="Confirmación caducada.", view=self)
            except discord.HTTPException:
                pass


class Suggestions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="sugerencia",
        description="Guarda una sugerencia o elimina una existente.",
    )
    @app_commands.describe(
        texto="Nueva sugerencia (máximo 240 caracteres)",
        borrar="ID de la sugerencia que quieres borrar",
    )
    async def suggestion(
        self,
        interaction: discord.Interaction,
        texto: app_commands.Range[str, 1, 240] | None = None,
        borrar: app_commands.Range[int, 1] | None = None,
    ) -> None:
        if (texto is None) == (borrar is None):
            await interaction.response.send_message(
                "Indica texto para crear una sugerencia o borrar con su ID.",
                ephemeral=True,
            )
            return

        if texto is not None:
            clean_text = texto.strip()
            if not clean_text:
                await interaction.response.send_message(
                    "La sugerencia no puede estar vacía.",
                    ephemeral=True,
                )
                return

            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    "INSERT INTO SUGERENCIAS (texto_sugerencia) VALUES (?)",
                    (clean_text,),
                )
                await db.commit()
                suggestion_id = cursor.lastrowid

            await interaction.response.send_message(
                f"Sugerencia #{suggestion_id} guardada correctamente.",
                ephemeral=True,
            )
            return

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(
                "Necesitas el permiso Gestionar mensajes para borrar sugerencias.",
                ephemeral=True,
            )
            return

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT texto_sugerencia FROM SUGERENCIAS WHERE id_sugerencia = ?",
                (borrar,),
            ) as cursor:
                row = await cursor.fetchone()

        if row is None:
            await interaction.response.send_message(
                f"No existe la sugerencia #{borrar}.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"¿Borrar la sugerencia #{borrar}?",
            description=row[0],
            color=discord.Color.orange(),
        )
        view = ConfirmDeleteView(interaction.user.id, borrar)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        view.message = await interaction.original_response()

    @app_commands.command(
        name="listar",
        description="Lista información almacenada por el bot.",
    )
    @app_commands.describe(tipo="Contenido que quieres listar")
    @app_commands.choices(
        tipo=[
            app_commands.Choice(name="sugerencias", value="sugerencias"),
            app_commands.Choice(name="mods", value="mods"),
        ]
    )
    async def list_items(
        self,
        interaction: discord.Interaction,
        tipo: app_commands.Choice[str],
    ) -> None:
        if tipo.value == "mods":
            bridge = getattr(self.bot, "project_zomboid_bridge", None)
            if bridge is None or not bridge.enabled:
                await interaction.response.send_message(
                    "La integración de Project Zomboid no está configurada.",
                    ephemeral=True,
                )
                return

            await interaction.response.defer(thinking=True)
            try:
                mods = await bridge.get_installed_mods()
            except Exception:
                logger.exception("No se pudo consultar la lista de mods")
                await interaction.followup.send(
                    "No se pudo consultar la lista de mods del servidor.",
                    ephemeral=True,
                )
                return

            if not mods:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="Mods instalados",
                        description="No hay mods instalados actualmente.",
                        color=discord.Color.blurple(),
                    )
                )
                return

            pages: list[str] = []
            current_page = ""
            for name in mods:
                line = "- " + discord.utils.escape_markdown(name) + chr(10)
                if current_page and len(current_page) + len(line) > 3800:
                    pages.append(current_page)
                    current_page = ""
                current_page += line
            if current_page:
                pages.append(current_page)

            embeds = []
            for index, page in enumerate(pages, start=1):
                embed = discord.Embed(
                    title="Mods instalados",
                    description=page,
                    color=discord.Color.blurple(),
                )
                footer = f"{len(mods)} mods"
                if len(pages) > 1:
                    footer += f" · Página {index} de {len(pages)}"
                embed.set_footer(text=footer)
                embeds.append(embed)

            for offset in range(0, len(embeds), 10):
                await interaction.followup.send(embeds=embeds[offset : offset + 10])
            return

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                """
                SELECT id_sugerencia, texto_sugerencia
                FROM SUGERENCIAS
                ORDER BY id_sugerencia
                """
            ) as cursor:
                suggestions = await cursor.fetchall()

        if not suggestions:
            await interaction.response.send_message(
                "Todavía no hay sugerencias guardadas.",
                ephemeral=True,
            )
            return

        pages: list[str] = []
        current_page = ""
        for suggestion_id, text in suggestions:
            line = f"**#{suggestion_id}** — {discord.utils.escape_markdown(text)}\n"
            if current_page and len(current_page) + len(line) > 3800:
                pages.append(current_page)
                current_page = ""
            current_page += line
        if current_page:
            pages.append(current_page)

        embeds = []
        for index, page in enumerate(pages, start=1):
            embed = discord.Embed(
                title="Sugerencias",
                description=page,
                color=discord.Color.blurple(),
            )
            if len(pages) > 1:
                embed.set_footer(text=f"Página {index} de {len(pages)}")
            embeds.append(embed)

        await interaction.response.defer()
        for offset in range(0, len(embeds), 10):
            await interaction.followup.send(embeds=embeds[offset : offset + 10])


async def setup(bot: commands.Bot) -> None:
    await initialize_database()
    await bot.add_cog(Suggestions(bot))