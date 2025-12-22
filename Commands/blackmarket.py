import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import sys
import os
import random
from datetime import datetime
from PIL import Image, ImageDraw
import io

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hola_db import is_user_registered
from db_utils import get_random_joint_by_rarity, update_user_currency, add_user_porro, get_user_balance

# Configuration
# Assuming rarity 1-4.
# Prices: R1=30€, R2=70€, R3=250€, R4=1000€
PRICES = {1: 30, 2: 70, 3: 250, 4: 1000}

class BlackMarketView(View):
    def __init__(self, user_id: int, joints: list, expiry_hour: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.joints = joints
        self.expiry_hour = expiry_hour  # The hour this menu belongs to
        
        # Create buttons for each joint
        for i, joint in enumerate(joints):
            rarity = joint['rareza']
            price = PRICES.get(rarity, 9999)
            
            btn = Button(
                label=f"Buy #{i+1} ({price}€)",
                style=discord.ButtonStyle.danger,
                custom_id=f"buy_bm_{i}"
            )
            btn.callback = self.create_buy_callback(i, joint, price)
            self.add_item(btn)

    def create_buy_callback(self, index, joint, price):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("No hables con mi camello, búscate el tuyo.", ephemeral=True)
                return

            # Check expiry (Cross-hour check)
            current_hour = datetime.now().hour
            if current_hour != self.expiry_hour:
                await interaction.response.send_message("El mercado ha cambiado. Usa /blackmarket de nuevo.", ephemeral=True)
                return

            # Confirmation View
            embed = discord.Embed(
                title="Confirmar Compra",
                description=f"¿Estás seguro de comprar **{joint['nombre']}** por **{price}€**?",
                color=discord.Color.dark_red()
            )
            confirm_view = ConfirmPurchaseView(self.user_id, joint, price)
            await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)
        return callback

class ConfirmPurchaseView(View):
    def __init__(self, user_id, joint, price):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.joint = joint
        self.price = price

    @discord.ui.button(label="Comprar", style=discord.ButtonStyle.success)
    async def buy(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            return

        # Re-check balance
        balance = await get_user_balance(self.user_id)
        if balance < self.price:
            await interaction.response.edit_message(content="No tienes suficiente pasta.", embed=None, view=None)
            return

        # Deduct money
        await update_user_currency(self.user_id, euros=-self.price)
        
        # Add joint
        # Assuming joint['id'] is available directly or we need to pass it
        await add_user_porro(self.user_id, self.joint['id'])
        
        await interaction.response.edit_message(
            content=f"Has comprado **{self.joint['nombre']}**! Se ha añadido a tu colección.",
            embed=None, view=None
        )

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            return

        await interaction.response.edit_message(content="Compra cancelada.", embed=None, view=None)

def create_market_image(joints):
    """
    Creates a 3-column image with black grid.
    """
    # 3 joints side by side
    # Size per joint: 200x200?
    w, h = 200, 200
    border = 10
    total_w = (w * 3) + (border * 4) # border | J1 | border | J2 | border | J3 | border
    total_h = h + (border * 2)
    
    img = Image.new('RGB', (total_w, total_h), color='black')
    
    for i, joint in enumerate(joints):
        # Load joint image
        # Assuming path is Images/Edition/id.png ? 
        # Need to know folder based on edition. 
        # Edition map (from cali.py context):
        # PAR -> The Park Bangers
        # SEM -> Sweet Semsem
        # DLX -> Deluxe
        edition_map = {
            'PAR': 'The Park Bangers',
            'SEM': 'Sweet Semsem',
            'DLX': 'Deluxe' # Guessing
        }
        folder = edition_map.get(joint['edicion'], 'The Park Bangers') # Fallback
        
        path = os.path.join("Images", folder, f"{joint['id']}.png")
        
        if os.path.exists(path):
            j_img = Image.open(path).convert("RGBA").resize((w, h))
        else:
            j_img = Image.new('RGB', (w, h), color='gray')
            d = ImageDraw.Draw(j_img)
            d.text((10,10), "No IMG", fill="white")
            
        x = border + (i * (w + border))
        y = border
        img.paste(j_img, (x, y))
        
    output = io.BytesIO()
    img.save(output, format='PNG')
    output.seek(0)
    return output

class BlackMarket(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="blackmarket", description="Mercado negro de porros. Cambia cada hora.")
    async def blackmarket(self, interaction: discord.Interaction):
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message("No te conozco. /start", ephemeral=True)
            return

        # Seed random with current hour to ensure consistency for everyone/time
        # Or just current time so it's consistent for this call? 
        # User said: "The joints will change each hour... if you clic at 23:59... at 00:00 will show 3 differents"
        # This implies global state OR seeded random.
        # Seeded random is easier.
        now = datetime.now()
        seed_value = int(now.strftime("%Y%m%d%H"))
        
        # Use a local Random instance to not affect global state
        rng = random.Random(seed_value)
        
        selected_joints = []
        for _ in range(3):
            # Roll rarity based on user provided weights
            # R1: 50%, R2: 30%, R3: 15%, R4: 5%
            roll = rng.random() * 100
            if roll < 50: rarity = 1
            elif roll < 80: rarity = 2
            elif roll < 95: rarity = 3
            else: rarity = 4
            
            # Select random edition? "from the PORROS table".
            # Currently we have get_random_joint_by_rarity which takes edition.
            # We should probably pick a random edition too or search all.
            # get_random_joint_by_rarity uses specific edition. 
            # I'll randomly pick an edition for each slot or generic query? 
            # db_utils doesn't have "get random by rarity ONLY". 
            # I will assume Park Bangers (PAR) mainly or random between available.
            edition = rng.choice(['PAR', 'SEM']) # Add DLX if valid
            
            # Since get_random_joint_by_rarity uses DB random, we can't seed IT easily without changing sql.
            # BUT, we can just call it. If it uses SQL RANDOM(), it changes every time.
            # Requirement: "The joints will change each hour".
            # If I call SQL `ORDER BY RANDOM()`, it changes every CALL.
            # To pin it to the hour, I need to select it deterministically or cache it.
            # Given the constraints, I should probably cache it in memory or simpler:
            # Revert to Python selection if dataset is small, or accept that /blackmarket might show different items 
            # if multiple people call it in same hour? NO, "joints will change each hour".
            # Implicitly means same hour = same joints.
            pass

        # Since I cannot easily change the DB util to be seeded, and I want to avoid complex caching in this swift implementation:
        # I will IMPLEMENT the selection here using all joints fetched once? 
        # Or better: Just use random.choice on a list of IDs if I had them.
        
        # ACTUALLY, to strictly follow "change each hour", I should cache the result.
        # Cache format: { hour_timestamp: [list of joints] }
        
        current_hour_key = now.strftime("%Y-%m-%d-%H")
        if not hasattr(self, 'market_cache') or self.market_cache_key != current_hour_key:
            # Generate new market
            self.market_cache_key = current_hour_key
            self.market_cache = []
            
            # We need to fetch 3 joints.
            # Using the RNG to determine rarity/edition, but actual FETCH needs to be pinned?
            # If I query DB now, I get random. 
            # I'll just query 3 times and save it. Providing "consistent view for everyone" needs shared state.
            # stored in `self`.
            
            # We need to fetch 3 unique joints.
            attempts = 0
            while len(self.market_cache) < 3 and attempts < 15:
                attempts += 1
                roll = random.random() * 100 # Real random for generation time
                if roll < 50: rarity = 1
                elif roll < 80: rarity = 2
                elif roll < 95: rarity = 3
                else: rarity = 4
                
                edition = random.choice(['PAR', 'SEM'])
                
                joint = await get_random_joint_by_rarity(edition, rarity)
                # Retry if None (e.g. no rarity 4 in that edition)
                if not joint: 
                    edition = 'PAR' # Fallback
                    joint = await get_random_joint_by_rarity(edition, rarity)
                
                if joint:
                    joint_dict = dict(joint)
                    # Check for duplicates using ID
                    if not any(j['id'] == joint_dict['id'] for j in self.market_cache):
                        self.market_cache.append(joint_dict)

        joints = self.market_cache
        
        if not joints:
            await interaction.response.send_message("El mercado negro está cerrado (Error DB).", ephemeral=True)
            return

        # Generate Image
        image_data = create_market_image(joints)
        file = discord.File(image_data, filename="blackmarket.png")
        
        embed = discord.Embed(
            title="🌙 Black Market",
            description="Ofertas validas solo por esta hora.\n¡Compra antes de que pillen al camello!",
            color=discord.Color.dark_grey()
        )
        embed.set_image(url="attachment://blackmarket.png")
        
        view = BlackMarketView(interaction.user.id, joints, now.hour)
        await interaction.response.send_message(embed=embed, file=file, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(BlackMarket(bot))
