import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import sys
import os
import random
from PIL import Image
import io

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered
from db_utils import update_user_currency, get_user_balance

# Available items in the scratch game
ITEMS = ['bell', 'cherry', 'grape', 'diamond', 'lemon', 'orange', 'seven']
SCRATCH_FOLDER = os.path.join("Images", "Scratch Game")

# Prize mapping
PRIZES = {
    'cherry': 5,
    'grape': 5,
    'lemon': 5,
    'orange': 5,
    'bell': 20,
    'diamond': 100,
    'seven': 500
}

def generate_ticket_items():
    """
    Generates 5 random items for the ticket.
    Now we just randomize fully but ensure max 3 of same item to avoid 4 or 5.
    We removed the forced win logic to make it purely random based on probabilities below?
    Actually, user didn't specify probabilities, just prizes.
    To keep it fair/fun, we'll stick to a purely random generation but filter out impossible scenarios (4 or 5 same).
    Adjusted to be purely random selection for now, as user didn't specify weights.
    """
    while True:
        ticket = [random.choice(ITEMS) for _ in range(5)]
        
        # Check max occurrences
        counts = {i: ticket.count(i) for i in ticket}
        if max(counts.values()) <= 3:
            random.shuffle(ticket)
            return ticket

def create_ticket_image(items, scratched_positions):
    """
    Creates a scratch ticket image using Pillow.
    """
    # Image dimensions
    item_size = 200
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
        if os.path.exists(item_path):
            item_img = Image.open(item_path).convert("RGBA").resize((item_size, item_size))
        else:
            # Fallback for missing images
            item_img = Image.new('RGB', (item_size, item_size), color='red')

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
        self.scratches_remaining = 5  # User can scratch all 5? "Limiting the game to 3 scratches" was in history, but user Request says "command /rasca will cost 2 euros".
        # Re-reading prompt: "limiting the game to 3 scratches" was from OLD request history. Current request doesn't explicitly restrict scratches. 
        # But standard scratch cards usually let you scratch everything or have a limit. 
        # Previous implementation had limit, but for this "prize" check (3 of same), you typically scratch all to see if you won.
        # I'll let them scratch all 5 to see if they get 3 matching.
        
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
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("¡Este no es tu ticket!", ephemeral=True)
                return
            
            if self.game_over:
                await interaction.response.send_message("¡El juego ya ha terminado!", ephemeral=True)
                return
            
            if position in self.scratched_positions:
                await interaction.response.send_message("¡Ya has rascado esta posición!", ephemeral=True)
                return
            
            self.scratched_positions.add(position)
            
            # Disable button
            self.children[position].disabled = True
            self.children[position].style = discord.ButtonStyle.secondary
            
            # Generate new image
            image_data = create_ticket_image(self.items, self.scratched_positions)
            file = discord.File(image_data, filename="ticket.png")
            
            # Check win condition (3 of same revealed OR all scratched)
            # Actually, we should check if they WON as soon as 3 matching are revealed.
            winning_item = self.get_winning_item()
            
            if winning_item:
                self.game_over = True
                prize = PRIZES.get(winning_item, 0)
                await update_user_currency(self.user_id, euros=prize)
                
                embed = discord.Embed(
                    title="🎉 ¡HAS GANADO! 🎉",
                    description=f"¡Tres **{winning_item}**! \n💰 Premio: **{prize} €**",
                    color=discord.Color.gold()
                )
                embed.set_image(url="attachment://ticket.png")
                self.disable_all_buttons()
                await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
                
            elif len(self.scratched_positions) == 5:
                self.game_over = True
                embed = discord.Embed(
                    title="😢 Suerte la próxima",
                    description="No has conseguido premio esta vez.",
                    color=discord.Color.red()
                )
                embed.set_image(url="attachment://ticket.png")
                self.disable_all_buttons()
                await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
            else:
                embed = discord.Embed(
                    title="🎫 Rasca y Gana",
                    description=f"Sigue rascando... ({len(self.scratched_positions)}/5)",
                    color=discord.Color.blue()
                )
                embed.set_image(url="attachment://ticket.png")
                await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
                
        return callback

    def get_winning_item(self):
        revealed = [self.items[i] for i in self.scratched_positions]
        counts = {i: revealed.count(i) for i in revealed}
        for item, count in counts.items():
            if count >= 3:
                return item
        return None

    def disable_all_buttons(self):
        for child in self.children:
            child.disabled = True

class Rasca(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="rasca", description="Compra un rasca por 2€ y gana premios.")
    async def rasca(self, interaction: discord.Interaction):
        # Check registration
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado. Usa /start para empezar.",
                ephemeral=True
            )
            return

        # Check balance
        balance = await get_user_balance(interaction.user.id)
        if balance < 2:
            await interaction.response.send_message(
                f"No tienes suficiente dinero. Cuesta 2€ y tienes {balance}€.",
                ephemeral=True
            )
            return

        # Deduct cost
        await update_user_currency(interaction.user.id, euros=-2)

        # Generate ticket
        items = generate_ticket_items()
        image_data = create_ticket_image(items, set())
        file = discord.File(image_data, filename="ticket.png")

        embed = discord.Embed(
            title="🎫 Rasca y Gana",
            description="Has pagado **2€**.\n¡Rasca 3 figuras iguales para ganar!",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://ticket.png")

        view = ScratchTicketView(interaction.user.id, items)
        await interaction.response.send_message(embed=embed, file=file, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Rasca(bot))
