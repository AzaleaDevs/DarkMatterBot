import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import sys
import os
import random
from PIL import Image, ImageDraw
import io

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered
from db_utils import update_user_currency

# Available items in the scratch game
ITEMS = ['bell', 'cherry', 'grape', 'diamond', 'lemon', 'orange', 'seven']
SCRATCH_FOLDER = os.path.join("Images", "Scratch Game")

def generate_ticket_items():
    """
    Generates 5 random items for the ticket with the following rules:
    - 33% chance to have exactly 3 of the same item (winning ticket)
    - Maximum 3 of any single item (no 4 or 5 of a kind)
    - Items are placed in random positions
    """
    roll = random.random()
    
    if roll < 0.33:  # 33% chance for a winning ticket
        # Create a ticket with exactly 3 of one item
        winning_item = random.choice(ITEMS)
        remaining_items = [item for item in ITEMS if item != winning_item]
        
        # Fill the rest with 2 different items
        other_items = random.sample(remaining_items, 2)
        
        ticket = [winning_item, winning_item, winning_item] + other_items
    else:
        # Create a non-winning ticket
        # Strategy: ensure no item appears more than 2 times
        ticket = []
        available_items = ITEMS.copy()
        
        while len(ticket) < 5:
            item = random.choice(available_items)
            ticket.append(item)
            
            # Count occurrences
            count = ticket.count(item)
            if count >= 2:
                # Remove this item from available choices
                available_items = [i for i in available_items if i != item]
            
            # Safety check: if we run out of items, reset (shouldn't happen)
            if not available_items:
                available_items = ITEMS.copy()
    
    # Shuffle to randomize positions
    random.shuffle(ticket)
    return ticket

def create_ticket_image(items, scratched_positions):
    """
    Creates a scratch ticket image using Pillow.
    
    Args:
        items: List of 5 item names
        scratched_positions: Set of indices (0-4) that have been scratched
    
    Returns:
        BytesIO object containing the PNG image
    """
    # Image dimensions
    item_size = 200  # Each item is 200x200
    border_width = 5
    total_width = (item_size * 5) + (border_width * 6)
    total_height = item_size + (border_width * 2)
    
    # Create base image with black background
    img = Image.new('RGB', (total_width, total_height), color='black')
    
    # Load overlay images
    sinrasca_path = os.path.join(SCRATCH_FOLDER, "sinrasca.png")
    rasca_path = os.path.join(SCRATCH_FOLDER, "rasca.png")
    
    sinrasca = Image.open(sinrasca_path).convert("RGBA").resize((item_size, item_size))
    rasca = Image.open(rasca_path).convert("RGBA").resize((item_size, item_size))
    
    # Place each item
    for i, item_name in enumerate(items):
        x_pos = border_width + (i * (item_size + border_width))
        y_pos = border_width
        
        # Load item image
        item_path = os.path.join(SCRATCH_FOLDER, f"{item_name}.png")
        item_img = Image.open(item_path).convert("RGBA").resize((item_size, item_size))
        
        # Create a white background for this cell
        cell_bg = Image.new('RGB', (item_size, item_size), color='white')
        
        # Paste item on white background
        cell_bg.paste(item_img, (0, 0), item_img)
        
        # Determine overlay (scratched or not)
        if i in scratched_positions:
            # Scratched: show rasca.png overlay
            cell_bg.paste(rasca, (0, 0), rasca)
        else:
            # Not scratched: show sinrasca.png overlay
            cell_bg.paste(sinrasca, (0, 0), sinrasca)
        
        # Paste cell into main image
        img.paste(cell_bg, (x_pos, y_pos))
    
    # Save to BytesIO
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output

class ScratchTicketView(View):
    def __init__(self, user_id: int, items: list):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.items = items
        self.scratched_positions = set()
        self.scratches_remaining = 5
        self.game_over = False
        
        # Create 5 buttons
        for i in range(5):
            button = Button(
                label=str(i + 1),
                style=discord.ButtonStyle.primary,
                custom_id=f"scratch_{i}"
            )
            button.callback = self.create_scratch_callback(i)
            self.add_item(button)
    
    def create_scratch_callback(self, position: int):
        """Creates a callback function for a specific button"""
        async def callback(interaction: discord.Interaction):
            # Check if it's the correct user
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    "Este no es tu ticket!",
                    ephemeral=True
                )
                return
            
            # Check if game is over
            if self.game_over:
                await interaction.response.send_message(
                    "El juego ya ha terminado!",
                    ephemeral=True
                )
                return
            
            # Check if already scratched
            if position in self.scratched_positions:
                await interaction.response.send_message(
                    "Ya has rascado esta posición!",
                    ephemeral=True
                )
                return
            
            # Scratch the position
            self.scratched_positions.add(position)
            self.scratches_remaining -= 1
            
            # Disable the button
            self.children[position].disabled = True
            self.children[position].style = discord.ButtonStyle.secondary
            
            # Generate new image
            image_data = create_ticket_image(self.items, self.scratched_positions)
            file = discord.File(image_data, filename="ticket.png")
            
            # Check for win condition
            if self.check_win():
                self.game_over = True
                
                # Player wins!
                await update_user_currency(self.user_id, euros=50)
                
                # Find the winning item
                revealed_items = [self.items[i] for i in self.scratched_positions]
                item_counts = {item: revealed_items.count(item) for item in set(revealed_items)}
                winning_item = max(item_counts, key=item_counts.get)
                
                embed = discord.Embed(
                    title="🎉 ¡GANASTE! 🎉",
                    description=f"¡Has revelado 3 **{winning_item}**!\n\n💰 Has ganado **50 euros**!",
                    color=discord.Color.gold()
                )
                embed.set_image(url="attachment://ticket.png")
                
                # Disable all buttons
                for child in self.children:
                    child.disabled = True
                
                await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
            elif self.scratches_remaining == 0:
                # All scratched, no win
                self.game_over = True
                
                embed = discord.Embed(
                    title="😢 Sin suerte esta vez",
                    description=f"No has conseguido 3 iguales.\n\nRascaste: {', '.join([self.items[i] for i in self.scratched_positions])}",
                    color=discord.Color.red()
                )
                embed.set_image(url="attachment://ticket.png")
                
                # Disable all buttons
                for child in self.children:
                    child.disabled = True
                
                await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
            else:
                # Game continues
                embed = discord.Embed(
                    title="🎫 Rasca y Gana",
                    description=f"Posiciones rascadas: **{len(self.scratched_positions)}/5**\n\nNecesitas revelar 3 iguales para ganar 50 euros!",
                    color=discord.Color.blue()
                )
                embed.set_image(url="attachment://ticket.png")
                
                await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        
        return callback
    
    def check_win(self):
        """Check if player has revealed 3 of the same item"""
        if len(self.scratched_positions) < 3:
            return False
        
        revealed_items = [self.items[i] for i in self.scratched_positions]
        item_counts = {item: revealed_items.count(item) for item in set(revealed_items)}
        
        return any(count >= 3 for count in item_counts.values())

class Rasca(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rasca", description="Juega al rasca y gana! Revela 3 iguales para ganar 50 euros.")
    async def rasca(self, interaction: discord.Interaction):
        # Check if user is registered
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado en el barrio para poder usar estos comandos. Prueba a hacer /start",
                ephemeral=True
            )
            return
        
        # Generate ticket items
        items = generate_ticket_items()
        
        # Create initial image (all hidden)
        image_data = create_ticket_image(items, set())
        file = discord.File(image_data, filename="ticket.png")
        
        # Create embed
        embed = discord.Embed(
            title="🎫 Rasca y Gana",
            description="Presiona los botones para rascar!\nNecesitas revelar 3 iguales para ganar 50 euros!",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://ticket.png")
        
        # Create view with buttons
        view = ScratchTicketView(interaction.user.id, items)
        
        await interaction.response.send_message(embed=embed, file=file, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Rasca(bot))
