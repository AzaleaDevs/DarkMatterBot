import asyncio
import os
from PIL import Image, ImageFilter, ImageOps
from db_utils import get_porros_by_edition, get_user_porros, add_user_porro

# Mock data for testing
TEST_EDITION = "PAR"
TEST_USER_ID = 123456789

async def verify_caja():
    print("Verifying Caja Image Generation...")
    
    # Ensure we have some data
    # Add a few joints to the user
    # await add_user_porro(TEST_USER_ID, 1) # Owns ID 1
    # await add_user_porro(TEST_USER_ID, 5) # Owns ID 5
    # await add_user_porro(TEST_USER_ID, 10) # Owns ID 10
    
    # Fetch all joints
    all_joints = await get_porros_by_edition(TEST_EDITION)
    print(f"Found {len(all_joints)} joints for edition {TEST_EDITION}")
    
    # Fetch user joints
    user_joints = await get_user_porros(TEST_USER_ID, TEST_EDITION)
    print(f"User owns: {list(user_joints.keys())}")
    
    # Generate Image Logic (Copied from caja.py for testing)
    # Generate Image Logic (Copied from caja.py for testing)
    base_image = Image.new('RGBA', (1024, 1024), (0, 0, 0, 255))
    grid_size = 5
    cell_size = 1024 // grid_size # 204
    img_size = 196
    offset = (cell_size - img_size) // 2
    
    # Calculate centering offset for the whole grid
    grid_offset_x = (1024 - (cell_size * grid_size)) // 2
    grid_offset_y = (1024 - (cell_size * grid_size)) // 2
    
    sorted_joints = sorted(all_joints, key=lambda x: x['id'])

    for index, joint in enumerate(sorted_joints):
        if index >= 25: break

        joint_id = joint['id']
        row = index // grid_size
        col = index % grid_size
        x = grid_offset_x + col * cell_size + offset
        y = grid_offset_y + row * cell_size + offset

        image_path = os.path.join("Images", "The Park Bangers", f"{joint_id}.png")
        
        if os.path.exists(image_path):
            try:
                img = Image.open(image_path).convert("RGBA")
                img = img.resize((img_size, img_size))

                if joint_id in user_joints:
                    base_image.paste(img, (x, y), img)
                else:
                    grey_img = ImageOps.grayscale(img)
                    grey_img = grey_img.convert("RGBA")
                    blurred_img = grey_img.filter(ImageFilter.GaussianBlur(radius=10))
                    base_image.paste(blurred_img, (x, y), img)
            except Exception as e:
                print(f"Error: {e}")
        else:
            print(f"Missing image: {image_path}")

    base_image.save("verify_caja_output.png")
    print("Image saved to verify_caja_output.png")

if __name__ == "__main__":
    asyncio.run(verify_caja())
