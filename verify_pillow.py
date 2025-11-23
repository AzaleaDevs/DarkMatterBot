from PIL import Image, ImageDraw, ImageFont
import os

def test_pillow(text):
    print(f"Testing with text: {text}")
    # Validation logic from bot
    if len(text) > 20:
        print("❌ Text too long")
        return
    
    if " " in text:
        print("❌ Text contains spaces")
        return

    # Image generation logic from bot
    width, height = 500, 500
    background_color = (0, 0, 255) # Blue
    text_color = (0, 0, 0) # Black
    
    image = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", 60)
        print("Loaded arial.ttf")
    except IOError:
        font = ImageFont.load_default()
        print("Loaded default font")
        
    try:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
    except AttributeError:
        text_width, text_height = draw.textsize(text, font=font)

    x = (width - text_width) / 2
    y = (height - text_height) / 2
    
    draw.text((x, y), text, fill=text_color, font=font)
    
    output_file = "test_pillow_output.png"
    image.save(output_file)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    test_pillow("Hello")
    test_pillow("TooLongTextForTheLimit")
    test_pillow("Two Words")
