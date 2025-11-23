import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io

class Pillow(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pillow", description="Genera una imagen con texto.")
    @app_commands.describe(text="Texto para la imagen (máx 20 letras, una sola palabra)")
    async def pillow(self, interaction: discord.Interaction, text: str):
        # Validation
        if len(text) > 20:
            await interaction.response.send_message("❌ El texto no puede tener más de 20 letras.", ephemeral=True)
            return
        
        if " " in text:
            await interaction.response.send_message("❌ El texto debe ser una sola palabra.", ephemeral=True)
            return

        # Image generation
        width, height = 500, 500
        background_color = (0, 0, 255) # Blue
        text_color = (0, 0, 0) # Black
        
        image = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except IOError:
            font = ImageFont.load_default()
            
        # Calculate text position to center it
        try:
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            text_width = right - left
            text_height = bottom - top
        except AttributeError:
             # Fallback for older Pillow versions
            text_width, text_height = draw.textsize(text, font=font)

        x = (width - text_width) / 2
        y = (height - text_height) / 2
        
        draw.text((x, y), text, fill=text_color, font=font)
        
        # Save to buffer
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        file = discord.File(buffer, filename="pillow.png")
        await interaction.response.send_message(file=file)




async def setup(bot: commands.Bot):
    await bot.add_cog(Pillow(bot))
