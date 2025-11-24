import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import sys
import os
import random

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import get_random_porro

class OpenButton(Button):
    def __init__(self):
        super().__init__(label="Open", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        # Get random porro from DB
        porro = await get_random_porro()
        
        if not porro:
            await interaction.response.send_message("Error: No items found in database.", ephemeral=True)
            return

        # Unpack data
        # Schema: id, nombre, descripcion, edicion
        p_id = porro['id']
        p_nombre = porro['nombre']
        p_descripcion = porro['descripcion']
        p_edicion = porro['edicion']

        # Create new embed
        embed = discord.Embed(title="Cali Pack Opened!", color=discord.Color.gold())
        embed.add_field(name="Name", value=p_nombre, inline=False)
        embed.add_field(name="Description", value=p_descripcion, inline=False)
        embed.add_field(name="Cali Pack", value=p_edicion, inline=False)

        # Image path
        # Assuming images are in Images/The Park Bangers/{id}.png
        image_path = os.path.join("Images", "The Park Bangers", f"{p_id}.png")
        
        if os.path.exists(image_path):
            file = discord.File(image_path, filename=f"{p_id}.png")
            embed.set_image(url=f"attachment://{p_id}.png")
            
            # Update the message with new embed and remove the button
            await interaction.response.edit_message(embed=embed, attachments=[file], view=None)
        else:
            await interaction.response.send_message(f"Error: Image {p_id}.png not found.", ephemeral=True)

class Cali(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="cali", description="Abre un Cali Pack y descubre qué te toca.")
    async def cali(self, interaction: discord.Interaction):
        # Initial Embed
        embed = discord.Embed(title="Cali Pack", description="Click Open to reveal!", color=discord.Color.blue())
        embed.add_field(name="Name", value="???", inline=False)
        embed.add_field(name="Description", value="???", inline=False)
        embed.add_field(name="Cali Pack", value="???", inline=False)
        
        # Initial Image
        initial_image_path = os.path.join("Images", "The Park Bangers", "loot_parkbangers.png")
        
        if os.path.exists(initial_image_path):
            file = discord.File(initial_image_path, filename="loot_parkbangers.png")
            embed.set_image(url="attachment://loot_parkbangers.png")
            
            view = View()
            view.add_item(OpenButton())
            
            await interaction.response.send_message(embed=embed, file=file, view=view)
        else:
            await interaction.response.send_message("Error: Initial image 'loot_parkbangers.png' not found in 'Images/The Park Bangers/'.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Cali(bot))
