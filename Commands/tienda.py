import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered
from db_utils import get_user_balance, update_user_currency, update_user_cali_pack

class TiendaView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        
        # Regular buttons
        self.park_button = Button(
            label="Park Bangers (15€)", 
            style=discord.ButtonStyle.primary,
            custom_id="buy_park"
        )
        self.park_button.callback = self.buy_park_callback
        self.add_item(self.park_button)
        
        self.semsem_button = Button(
            label="Sweet Semsem (15€)", 
            style=discord.ButtonStyle.primary,
            custom_id="buy_semsem"
        )
        self.semsem_button.callback = self.buy_semsem_callback
        self.add_item(self.semsem_button)

    async def buy_park_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Esta no es tu tienda.", ephemeral=True)
            return

        # Show confirmation with image
        view = ConfirmView(self.user_id, "Park Bangers", 15, "cali_park")
        
        embed = discord.Embed(
            title="Confirmar Compra",
            description="¿Quieres comprar un **Cali Pack - Park Bangers** por **15€**?",
            color=discord.Color.gold()
        )
        
        # Load image
        file = None
        if os.path.exists("Images/The Park Bangers/loot_parkbangers.png"):
            file = discord.File("Images/The Park Bangers/loot_parkbangers.png", filename="loot.png")
            embed.set_image(url="attachment://loot.png")
            
        if file:
            await interaction.response.edit_message(embed=embed, view=view, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])

    async def buy_semsem_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Esta no es tu tienda.", ephemeral=True)
            return

        # Show confirmation with image
        view = ConfirmView(self.user_id, "Sweet Semsem", 15, "cali_semsem")
        
        embed = discord.Embed(
            title="Confirmar Compra",
            description="¿Quieres comprar un **Cali Pack - Sweet Semsem** por **15€**?",
            color=discord.Color.gold()
        )
        
        # Load image
        file = None
        if os.path.exists("Images/Sweet Semsem/loot_sweetsemsem.png"):
            file = discord.File("Images/Sweet Semsem/loot_sweetsemsem.png", filename="loot.png")
            embed.set_image(url="attachment://loot.png")
            
        if file:
            await interaction.response.edit_message(embed=embed, view=view, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])

class ConfirmView(View):
    def __init__(self, user_id: int, item_name: str, price: int, pack_type: str):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.item_name = item_name
        self.price = price
        self.pack_type = pack_type
        
        yes_btn = Button(label="YES", style=discord.ButtonStyle.success)
        yes_btn.callback = self.yes_callback
        self.add_item(yes_btn)
        
        no_btn = Button(label="NO", style=discord.ButtonStyle.danger)
        no_btn.callback = self.no_callback
        self.add_item(no_btn)

    async def yes_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return

        balance = await get_user_balance(self.user_id)
        if balance < self.price:
            await interaction.response.send_message("No tienes suficiente dinero.", ephemeral=True)
            # Return to shop
            embed = await self.get_shop_embed(interaction.user)
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=TiendaView(self.user_id), attachments=[])
            return

        # Process transaction
        await update_user_currency(self.user_id, euros=-self.price)
        await update_user_cali_pack(self.user_id, self.pack_type, 1)
        
        # Return to main shop view FIRST (to remove buttons)
        embed = await self.get_shop_embed(interaction.user)
        # Remove attachments (previous image)
        await interaction.response.edit_message(embed=embed, view=TiendaView(self.user_id), attachments=[])
        
        # Then send ephemeral success message
        await interaction.followup.send(f"Has comprado **{self.item_name}**!", ephemeral=True)

    async def no_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return
            
        # Cancel and return to shop
        embed = await self.get_shop_embed(interaction.user)
        await interaction.response.edit_message(embed=embed, view=TiendaView(self.user_id), attachments=[])

    async def get_shop_embed(self, user):
        balance = await get_user_balance(user.id)
        embed = discord.Embed(
            title="420 CALISHOP",
            description=f"Dinero de {user.name} : {balance} €",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Items Disponibles", value="• Cali pack The Park Bangers - 15€\n• Cali pack Sweet Semsem - 15€", inline=False)
        return embed

class Tienda(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="tienda", description="Abre la tienda para comprar packs.")
    async def tienda(self, interaction: discord.Interaction):
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message("Regístrate con /start primero.", ephemeral=True)
            return

        balance = await get_user_balance(interaction.user.id)
        
        embed = discord.Embed(
            title="420 CALISHOP",
            description=f"Dinero de {interaction.user.name} : {balance} €",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="Items Disponibles", value="• Cali pack The Park Bangers - 15€\n• Cali pack Sweet Semsem - 15€", inline=False)
        
        view = TiendaView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tienda(bot))
