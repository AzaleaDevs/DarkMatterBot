import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import sys
import os
import random

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered
from db_utils import (
    get_user_cali_packs, 
    decrement_cali_pack, 
    get_random_joint_by_rarity,
    add_user_porro,
    update_user_currency
)

# Pack type configurations
PACK_CONFIGS = {
    'cali_park': {
        'name': 'Cali - The Park Bangers',
        'edition': 'PAR',
        'image_folder': 'The Park Bangers',
        'loot_image': 'loot_parkbangers.png',
        'guaranteed_joint': False
    },
    'cali_semsem': {
        'name': 'Cali - Sweet Semsem',
        'edition': 'SEM',
        'image_folder': 'Sweet Semsem',
        'loot_image': 'loot_sweetsemsem.png',
        'guaranteed_joint': False
    },
    'cali_dx': {
        'name': 'Cali - Deluxe',
        'edition': 'PAR',  # Using PAR for now, can be changed
        'image_folder': 'Deluxe',
        'loot_image': 'loot_deluxe.png',
        'guaranteed_joint': True
    }
}

def roll_rarity():
    """
    Rolls for joint rarity based on probabilities:
    Common (1): 48%
    Rare (2): 24%
    Epic (3): 16%
    Legendary (4): 12%
    """
    roll = random.random() * 100
    if roll < 48:
        return 1  # Common
    elif roll < 72:  # 48 + 24
        return 2  # Rare
    elif roll < 88:  # 72 + 16
        return 3  # Epic
    else:
        return 4  # Legendary

def roll_reward_type():
    """
    Rolls for reward type for non-guaranteed packs:
    Nothing: 5%
    5 Euros: 10%
    20 Kogos: 25%
    Joint: 60%
    """
    roll = random.random() * 100
    if roll < 5:
        return 'nothing'
    elif roll < 15:  # 5 + 10
        return 'euros'
    elif roll < 40:  # 15 + 25
        return 'kogos'
    else:
        return 'joint'

class PackSelectionView(View):
    def __init__(self, user_id: int, packs: dict):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.packs = packs
        
        # Create list of available packs
        self.available_packs = []
        for pack_type, count in packs.items():
            if count > 0:
                self.available_packs.append(pack_type)
        
        self.current_index = 0
        
        # Update button states
        self.update_button_states()
    
    def update_button_states(self):
        """Enable/disable navigation buttons based on available packs"""
        has_multiple = len(self.available_packs) > 1
        self.children[0].disabled = not has_multiple  # Previous button
        self.children[2].disabled = not has_multiple  # Next button
    
    def get_current_pack_type(self):
        """Get the currently selected pack type"""
        if self.available_packs:
            return self.available_packs[self.current_index]
        return None
    
    def get_pack_embed(self):
        """Generate embed for current pack"""
        pack_type = self.get_current_pack_type()
        if not pack_type:
            return None
        
        config = PACK_CONFIGS[pack_type]
        count = self.packs[pack_type]
        
        embed = discord.Embed(
            title=config['name'],
            description=f"Tienes **{count}** pack(s) disponible(s)\n\nPresiona 🎁 para abrir uno!",
            color=discord.Color.gold()
        )
        
        return embed, config
    
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def previous_pack(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este no es tu inventario.", ephemeral=True)
            return
        
        if len(self.available_packs) > 1:
            self.current_index = (self.current_index - 1) % len(self.available_packs)
            embed, config = self.get_pack_embed()
            
            # Try to load image
            image_path = os.path.join("Images", config['image_folder'], config['loot_image'])
            if os.path.exists(image_path):
                file = discord.File(image_path, filename=config['loot_image'])
                embed.set_image(url=f"attachment://{config['loot_image']}")
                await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="🎁 Open", style=discord.ButtonStyle.success)
    async def open_pack(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("No molestes, este pack no es tuyo.", ephemeral=True)
            return

        pack_type = self.get_current_pack_type()
        if not pack_type:
            await interaction.response.send_message("Error: No pack selected", ephemeral=True)
            return
        
        config = PACK_CONFIGS[pack_type]
        
        # Decrement pack count
        success = await decrement_cali_pack(self.user_id, pack_type)
        if not success:
            await interaction.response.send_message("No tienes este pack disponible", ephemeral=True)
            return
        
        # Determine reward
        if config['guaranteed_joint']:
            reward_type = 'joint'
        else:
            reward_type = roll_reward_type()
        
        # Process reward
        if reward_type == 'nothing':
            embed = discord.Embed(
                title="¡Mala suerte!",
                description="No hay nada dentro! Te han timado!",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, attachments=[], view=None)
            
        elif reward_type == 'euros':
            await update_user_currency(self.user_id, euros=5)
            embed = discord.Embed(
                title="¡5 Euros!",
                description="Dentro había 5 eurillos que te vienen bien para pillarte un Monster y unas pipas",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, attachments=[], view=None)
            
        elif reward_type == 'kogos':
            await update_user_currency(self.user_id, kogos=20)
            embed = discord.Embed(
                title="¡20 Kogos!",
                description="Dentro encuentras 20 kogos, no está mal pero te decepciona que dentro no hubiese un porriqui",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=embed, attachments=[], view=None)
            
        else:  # joint
            # Roll rarity
            rarity = roll_rarity()
            
            # Get random joint
            joint = await get_random_joint_by_rarity(config['edition'], rarity)
            
            if not joint:
                await interaction.response.send_message(
                    f"Error: No se encontró ningún porro de rareza {rarity} en la edición {config['edition']}",
                    ephemeral=True
                )
                return
            
            # Save joint to user's collection
            await add_user_porro(self.user_id, joint['id'])
            
            # Create result embed
            rarity_names = {1: "Común", 2: "Raro", 3: "Épico", 4: "Legendario"}
            rarity_colors = {
                1: discord.Color.light_gray(),
                2: discord.Color.blue(),
                3: discord.Color.purple(),
                4: discord.Color.gold()
            }
            
            embed = discord.Embed(
                title="¡Cali Pack Abierto!",
                description=f"**{joint['nombre']}**",
                color=rarity_colors.get(rarity, discord.Color.green())
            )
            embed.add_field(name="Descripción", value=joint['descripcion'], inline=False)
            embed.add_field(name="Edición", value=config['name'], inline=True)
            embed.add_field(name="Rareza", value=rarity_names.get(rarity, "Desconocida"), inline=True)
            
            # Set pack image as thumbnail
            pack_image_path = os.path.join("Images", config['image_folder'], config['loot_image'])
            if os.path.exists(pack_image_path):
                pack_file = discord.File(pack_image_path, filename=f"pack_{config['loot_image']}")
                embed.set_thumbnail(url=f"attachment://pack_{config['loot_image']}")
            
            # Set joint image
            joint_image_path = os.path.join("Images", config['image_folder'], f"{joint['id']}.png")
            
            files = []
            if os.path.exists(pack_image_path):
                files.append(discord.File(pack_image_path, filename=f"pack_{config['loot_image']}"))
            
            if os.path.exists(joint_image_path):
                joint_file = discord.File(joint_image_path, filename=f"{joint['id']}.png")
                embed.set_image(url=f"attachment://{joint['id']}.png")
                files.append(joint_file)
            
            if files:
                await interaction.response.edit_message(embed=embed, attachments=files, view=None)
            else:
                await interaction.response.edit_message(embed=embed, attachments=[], view=None)
    
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next_pack(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Este no es tu inventario.", ephemeral=True)
            return

        if len(self.available_packs) > 1:
            self.current_index = (self.current_index + 1) % len(self.available_packs)
            embed, config = self.get_pack_embed()
            
            # Try to load image
            image_path = os.path.join("Images", config['image_folder'], config['loot_image'])
            if os.path.exists(image_path):
                file = discord.File(image_path, filename=config['loot_image'])
                embed.set_image(url=f"attachment://{config['loot_image']}")
                await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.defer()

class Cali(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="cali", description="Abre un Cali Pack y descubre qué te toca.")
    async def cali(self, interaction: discord.Interaction):
        # Check if user is registered
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado en el barrio para poder usar estos comandos. Prueba a hacer /start",
                ephemeral=True
            )
            return
        
        # Get user's cali packs
        packs = await get_user_cali_packs(interaction.user.id)
        
        if not packs:
            await interaction.response.send_message(
                "Error al cargar tu inventario",
                ephemeral=True
            )
            return
        
        # Check if user has any packs
        total_packs = packs['cali_park'] + packs['cali_dx'] + packs['cali_semsem']
        if total_packs == 0:
            await interaction.response.send_message(
                "No tienes cali packs para abrir",
                ephemeral=True
            )
            return
        
        # Create pack selection view
        view = PackSelectionView(interaction.user.id, packs)
        embed, config = view.get_pack_embed()
        
        # Try to load initial image
        image_path = os.path.join("Images", config['image_folder'], config['loot_image'])
        if os.path.exists(image_path):
            file = discord.File(image_path, filename=config['loot_image'])
            embed.set_image(url=f"attachment://{config['loot_image']}")
            await interaction.response.send_message(embed=embed, file=file, view=view)
        else:
            await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Cali(bot))
