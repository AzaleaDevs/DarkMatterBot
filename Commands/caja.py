import discord
from discord import app_commands
from discord.ext import commands
import sys
import os
from PIL import Image, ImageFilter, ImageOps
import io

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_utils import get_porros_by_edition, get_user_porros
from hola_db import is_user_registered

class Caja(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="caja", description="Muestra tu colección de porros de una edición.")
    @app_commands.describe(edicion="La edición de la colección (ej. PAR)")
    async def caja(self, interaction: discord.Interaction, edicion: str):
        # Check if user is registered
        if not await is_user_registered(interaction.user.id):
            await interaction.response.send_message(
                "Aún no estás registrado en el barrio para poder usar estos comandos. Prueba a hacer /start",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()

        # Fetch all joints for the edition
        all_joints = await get_porros_by_edition(edicion)
        
        if not all_joints:
            await interaction.followup.send(f"No se encontraron porros para la edición '{edicion}'.")
            return

        # Fetch user's owned joints
        user_joints = await get_user_porros(interaction.user.id, edicion)

        # Create base image (1024x1024) with black background for grid effect
        base_image = Image.new('RGBA', (1024, 1024), (0, 0, 0, 255))
        
        # Grid settings
        grid_size = 5
        cell_size = 1024 // grid_size # 204
        # Image size slightly smaller to create border
        img_size = 196
        offset = (cell_size - img_size) // 2
        
        # Calculate centering offset for the whole grid
        grid_offset_x = (1024 - (cell_size * grid_size)) // 2
        grid_offset_y = (1024 - (cell_size * grid_size)) // 2

        # Sort joints by ID to ensure consistent order (1-25)
        # Assuming IDs are sequential or we just want them ordered
        sorted_joints = sorted(all_joints, key=lambda x: x['id'])

        for index, joint in enumerate(sorted_joints):
            if index >= 25:
                break # Limit to 25 items for 5x5 grid

            joint_id = joint['id']
            
            # Calculate position
            row = index // grid_size
            col = index % grid_size
            x = grid_offset_x + col * cell_size + offset
            y = grid_offset_y + row * cell_size + offset

            # Load image
            image_path = os.path.join("Images", "The Park Bangers", f"{joint_id}.png")
            
            if os.path.exists(image_path):
                try:
                    img = Image.open(image_path).convert("RGBA")
                    img = img.resize((img_size, img_size))

                    # Check if user owns it
                    if joint_id in user_joints:
                        # Owned: Paste as is
                        base_image.paste(img, (x, y), img)
                    else:
                        # Not owned: Greyscale + Blur
                        grey_img = ImageOps.grayscale(img)
                        # Convert back to RGBA to maintain transparency if needed, or just paste
                        grey_img = grey_img.convert("RGBA")
                        
                        # Apply blur - Increased radius
                        blurred_img = grey_img.filter(ImageFilter.GaussianBlur(radius=10))
                        
                        # Apply transparency mask from original image to keep shape
                        base_image.paste(blurred_img, (x, y), img)
                except Exception as e:
                    print(f"Error processing image {image_path}: {e}")
            else:
                # Placeholder for missing image?
                pass

        # Save to buffer
        with io.BytesIO() as image_binary:
            base_image.save(image_binary, 'PNG')
            image_binary.seek(0)
            
            file = discord.File(fp=image_binary, filename=f"collection_{edicion}.png")
            
            embed = discord.Embed(title=f"Colección: {edicion}", color=discord.Color.purple())
            embed.set_image(url=f"attachment://collection_{edicion}.png")
            
            await interaction.followup.send(embed=embed, file=file)

async def setup(bot: commands.Bot):
    await bot.add_cog(Caja(bot))
