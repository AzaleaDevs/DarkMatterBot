import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ─── Load Pokémon data ───────────────────────────────────────────────────────
_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pokemon_data.json'))
with open(_DATA_PATH, encoding='utf-8') as _f:
    _POKE_DATA = json.load(_f)

# ─── Pre-compute weighted stat distribution ───────────────────────────────────
# 1–59: uncommon | 60–130: common | 131–190: rare
# 191–230: extremely rare | 231–255: very very rare
_STAT_VALUES: list[int] = []
_STAT_WEIGHTS: list[int] = []
for _start, _end, _w in [
    (1,   59,  30),
    (60,  130, 100),
    (131, 190, 20),
    (191, 230, 5),
    (231, 255, 1),
]:
    for _v in range(_start, _end + 1):
        _STAT_VALUES.append(_v)
        _STAT_WEIGHTS.append(_w)


def _rand_stat() -> int:
    return random.choices(_STAT_VALUES, weights=_STAT_WEIGHTS, k=1)[0]


def _safe_filename(name: str) -> str:
    """Return a Discord-safe attachment filename (no spaces or apostrophes)."""
    return name.replace(" ", "_").replace("'", "").replace("'", "")


# ─── Type emoji mapping ───────────────────────────────────────────────────────
_TYPE_EMOJI = {
    "Normal":    "⬜",
    "Fuego":     "🔥",
    "Agua":      "💧",
    "Planta":    "🌿",
    "Eléctrico": "⚡",
    "Hielo":     "❄️",
    "Lucha":     "🥊",
    "Veneno":    "☠️",
    "Tierra":    "🏔️",
    "Volador":   "🌬️",
    "Psíquico":  "🔮",
    "Bicho":     "🐛",
    "Roca":      "🪨",
    "Fantasma":  "👻",
    "Dragón":    "🐉",
    "Siniestro": "🌑",
    "Acero":     "⚙️",
    "Hada":      "✨",
}


class SoyPoke(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pokes_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'Pokes')
        )

    @app_commands.command(
        name="soypoke",
        description="¡Descubre cuál sería tu Pokémon!"
    )
    async def soypoke(self, interaction: discord.Interaction):
        if not os.path.exists(self.pokes_path):
            await interaction.response.send_message(
                "No encuentro la carpeta de Pokes.", ephemeral=True
            )
            return

        files = [
            f for f in os.listdir(self.pokes_path)
            if os.path.isfile(os.path.join(self.pokes_path, f))
        ]
        if not files:
            await interaction.response.send_message(
                "La carpeta de Pokes está vacía.", ephemeral=True
            )
            return

        # ── Pick random Pokémon image ─────────────────────────────────────────
        raw_filename = random.choice(files)
        file_path    = os.path.join(self.pokes_path, raw_filename)
        safe_name    = _safe_filename(raw_filename)
        pokemon_name = os.path.splitext(raw_filename)[0]

        # ── Random data ───────────────────────────────────────────────────────
        hab1, hab2   = random.sample(_POKE_DATA["habilidades"], 2)
        objeto       = random.choice(_POKE_DATA["objetos"])
        tipo1, tipo2 = random.sample(_POKE_DATA["tipos"], 2)
        moveset      = random.sample(_POKE_DATA["ataques"], 4)

        # ── Stats ─────────────────────────────────────────────────────────────
        ps          = _rand_stat()
        ataque      = _rand_stat()
        atq_esp     = _rand_stat()
        defensa     = _rand_stat()
        def_esp     = _rand_stat()
        velocidad   = _rand_stat()

        # ── Build embed ───────────────────────────────────────────────────────
        embed = discord.Embed(
            title="¡Este es tu Pokémon!",
            description=f"**{interaction.user.display_name}** ha descubierto su forma Pokémon 👀",
            color=discord.Color.random()
        )
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url
        )

        # Habilidades
        embed.add_field(name="⚡ Habilidad",        value=hab1, inline=True)
        embed.add_field(name="🔒 Habilidad Oculta", value=hab2, inline=True)
        embed.add_field(name="\u200b",              value="\u200b", inline=False)

        # Objeto y tipos
        t1_label = f"{_TYPE_EMOJI.get(tipo1, '')} {tipo1}"
        t2_label = f"{_TYPE_EMOJI.get(tipo2, '')} {tipo2}"
        embed.add_field(name="🎒 Objeto Equipado", value=objeto,   inline=True)
        embed.add_field(name="\u200b",             value="\u200b", inline=True)
        embed.add_field(name="\u200b",             value="\u200b", inline=False)
        embed.add_field(name="Tipo 1",             value=t1_label, inline=True)
        embed.add_field(name="Tipo 2",             value=t2_label, inline=True)
        embed.add_field(name="\u200b",             value="\u200b", inline=False)

        # Ataques
        attacks_text = "\n".join(f"> {i+1}. **{m}**" for i, m in enumerate(moveset))
        embed.add_field(name="⚔️ Ataques", value=attacks_text, inline=False)

        # Stats
        stats_text = (
            f"❤️ **PS:**                  `{ps}`\n"
            f"⚔️ **Ataque:**              `{ataque}`\n"
            f"🔥 **Ataque Especial:**     `{atq_esp}`\n"
            f"🛡️ **Defensa:**             `{defensa}`\n"
            f"✨ **Defensa Especial:**    `{def_esp}`\n"
            f"💨 **Velocidad:**           `{velocidad}`"
        )
        embed.add_field(name="📊 Stats", value=stats_text, inline=False)

        embed.set_footer(text=f"Pokémon: {pokemon_name}")
        embed.set_image(url=f"attachment://{safe_name}")

        discord_file = discord.File(file_path, filename=safe_name)
        await interaction.response.send_message(embed=embed, file=discord_file)


async def setup(bot: commands.Bot):
    await bot.add_cog(SoyPoke(bot))
