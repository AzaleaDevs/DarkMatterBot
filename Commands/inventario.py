import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import sys
import os
import math

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered
from db_utils import get_user_inventory, get_user_joints_paginated

class InventoryView(View):
    def __init__(self, user_id: int, username: str, avatar_url: str):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.username = username
        self.avatar_url = avatar_url
        self.current_page = 0
        self.max_page = 0
        
    async def get_page_embed(self):
        """Generate embed for current page"""
        if self.current_page == 0:
            # Page 1: Currency and Cali Packs
            inventory = await get_user_inventory(self.user_id)
            
            if not inventory:
                embed = discord.Embed(
                    title=f"Inventario de {self.username}",
                    description="Error al cargar el inventario",
                    color=discord.Color.red()
                )
                return embed
            
            embed = discord.Embed(
                title=f"Inventario de {self.username}",
                description="💰 **Recursos y Cali Packs**",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=self.avatar_url)
            
            # Currency section
            embed.add_field(
                name="💵 Monedas",
                value=(
                    f"**Euros:** {inventory['euros']}\n"
                    f"**Kogos:** {inventory['kogos']}"
                ),
                inline=False
            )
            
            # Cali Packs section
            embed.add_field(
                name="🎁 Cali Packs",
                value=(
                    f"**Cali - The Park Bangers:** {inventory['cali_park']}\n"
                    f"**Cali - Deluxe:** {inventory['cali_dx']}\n"
                    f"**Cali - Sweet Semsem:** {inventory['cali_semsem']}"
                ),
                inline=False
            )
            
            embed.set_footer(text="Página 1 | Usa las flechas para navegar")
            
        else:
            # Page 2+: Joints
            joints_per_page = 25
            offset = (self.current_page - 1) * joints_per_page
            
            joints, total = await get_user_joints_paginated(self.user_id, offset, joints_per_page)
            
            # Calculate max page
            self.max_page = math.ceil(total / joints_per_page) if total > 0 else 0
            
            embed = discord.Embed(
                title=f"Inventario de {self.username}",
                description="🌿 **Colección de Porros**",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=self.avatar_url)
            
            if joints:
                joints_text = "\n".join([f"**{name}** x{cantidad}" for name, cantidad in joints])
                embed.add_field(
                    name="Porros en posesión",
                    value=joints_text,
                    inline=False
                )
            else:
                embed.add_field(
                    name="Porros en posesión",
                    value="No tienes porros aún. ¡Abre algunos Cali Packs!",
                    inline=False
                )
            
            embed.set_footer(text=f"Página {self.current_page + 1} | Total de porros: {total}")
        
        return embed
    
    async def update_buttons(self):
        """Update button states based on current page"""
        # Calculate total pages
        joints, total = await get_user_joints_paginated(self.user_id, 0, 25)
        joints_per_page = 25
        total_joint_pages = math.ceil(total / joints_per_page) if total > 0 else 0
        total_pages = 1 + total_joint_pages  # 1 for currency page + joint pages
        
        # Disable/enable buttons
        self.children[0].disabled = (self.current_page == 0)  # Back button
        self.children[1].disabled = (self.current_page >= total_pages - 1)  # Forward button
    
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_buttons()
            embed = await self.get_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        # Check if there are more pages
        joints, total = await get_user_joints_paginated(self.user_id, 0, 25)
        joints_per_page = 25
        total_joint_pages = math.ceil(total / joints_per_page) if total > 0 else 0
        total_pages = 1 + total_joint_pages
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
            await self.update_buttons()
            embed = await self.get_page_embed()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

class Inventario(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="inventario", description="Muestra tu inventario de items y porros.")
    async def inventario(self, interaction: discord.Interaction):
        # Check if user is registered
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado en el barrio para poder usar estos comandos. Prueba a hacer /start",
                ephemeral=True
            )
            return
        
        # Create view and get initial embed
        view = InventoryView(
            interaction.user.id,
            interaction.user.name,
            interaction.user.display_avatar.url
        )
        
        await view.update_buttons()
        embed = await view.get_page_embed()
        
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Inventario(bot))
