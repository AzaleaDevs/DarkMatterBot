from PIL import Image, ImageDraw, ImageFont
import os

def generate_meme(text):
    try:
        # Load image
        image_path = os.path.join(os.getcwd(), "Images", "meme.jpg")
        if not os.path.exists(image_path):
            print(f"❌ No se encontró la imagen base (Images/meme.jpg). Path: {image_path}")
            return
            
        with Image.open(image_path) as img:
            img = img.convert("RGBA")
            width, height = img.size
            draw = ImageDraw.Draw(img)
            
            # Font setup
            font_size = 60
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except IOError:
                font = ImageFont.load_default()
                font_size = 20 # Default font is small
            
            # Wrap text
            lines = []
            words = text.split()
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_w = bbox[2] - bbox[0]
                
                if text_w < width - 40: # 20px padding on each side
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Word is too long, force split or just add it
                        lines.append(word)
                        current_line = []
            if current_line:
                lines.append(' '.join(current_line))
            
            # Calculate total height
            line_heights = []
            total_text_height = 0
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                h = bbox[3] - bbox[1]
                line_heights.append(h)
                total_text_height += h + 10 # 10px line spacing
            
            if line_heights:
                total_text_height -= 10 # Remove last spacing
            
            start_y = (height - total_text_height) / 2
            
            # Prepare gradient
            gradient = Image.new('RGBA', (width, height), (0,0,0,0))
            g_draw = ImageDraw.Draw(gradient)
            
            # Gradient bounds
            text_area_top = int(start_y)
            text_area_bottom = int(start_y + total_text_height)
            
            # FIX: Draw gradient slightly larger to cover potential rendering overflows
            # and clamp the ratio calculation.
            draw_start = max(0, text_area_top - 10)
            draw_end = min(height, text_area_bottom + 20) # Extra padding at bottom

            for y in range(draw_start, draw_end):
                # Ratio 0 to 1 relative to the TEXT AREA
                if text_area_bottom - text_area_top == 0:
                    ratio = 0
                else:
                    ratio = (y - text_area_top) / (text_area_bottom - text_area_top)
                
                # Clamp ratio to ensure valid colors if we go outside bounds
                ratio = max(0.0, min(1.0, ratio))
                
                # Blue (0, 0, 255) to Pink (255, 105, 180)
                r = int(0 * (1 - ratio) + 255 * ratio)
                g = int(0 * (1 - ratio) + 105 * ratio)
                b = int(255 * (1 - ratio) + 180 * ratio)
                
                g_draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

            # Draw text
            current_y = start_y
            
            # 1. Draw Stroke (Black) directly on image
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_w = bbox[2] - bbox[0]
                text_x = (width - text_w) / 2
                
                # Draw stroke
                draw.text((text_x, current_y), line, font=font, fill="black", stroke_width=4, stroke_fill="black")
                
                current_y += line_heights[i] + 10

            # 2. Draw Text Mask for Gradient
            mask = Image.new('L', (width, height), 0)
            mask_draw = ImageDraw.Draw(mask)
            
            current_y = start_y
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                text_w = bbox[2] - bbox[0]
                text_x = (width - text_w) / 2
                
                # Draw white text on black mask
                mask_draw.text((text_x, current_y), line, font=font, fill=255)
                current_y += line_heights[i] + 10
            
            # 3. Composite Gradient
            gradient_text = Image.composite(gradient, Image.new('RGBA', (width, height), (0,0,0,0)), mask)
            img.alpha_composite(gradient_text)
            
            # Save
            img.save("test_meme_output.png")
            print("✅ test_meme_output.png generated successfully.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_meme("This is a test meme with a very long text to check if wrapping works correctly and the gradient looks good.")
