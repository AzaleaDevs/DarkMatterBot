import asyncio
import sys
import os

sys.path.append(os.path.dirname(__file__))

from hola_db import is_user_registered

async def test_check():
    # Test with a user ID that definitely doesn't exist
    test_id = 123456789012345
    result = await is_user_registered(test_id)
    print(f"User {test_id} registered: {result}")
    print(f"Type: {type(result)}")
    
    # Check the actual query
    import aiosqlite
    DB_PATH = os.path.join("Databases", "darkmatter_pro.db")
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM USUARIOS WHERE id = ?", (test_id,)) as cursor:
            row = await cursor.fetchone()
            print(f"Raw query result: {row}")
            print(f"Row is None: {row is None}")
            print(f"Row is not None: {row is not None}")

if __name__ == "__main__":
    asyncio.run(test_check())
