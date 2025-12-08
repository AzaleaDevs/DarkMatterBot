import aiosqlite
import os

DB_PATH = os.path.join("Databases", "darkmatter_pro.db")

async def is_user_registered(user_id: int):
    """
    Checks if a user exists in the USUARIOS table.
    Returns True if user exists, False otherwise.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM USUARIOS WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def get_user_data(user_id: int):
    """
    Fetches complete user data from USUARIOS table.
    Returns the user row if found, else None.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM USUARIOS WHERE id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()

async def register_user(user_id: int, name: str):
    """
    Registers a new user in the USUARIOS table.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO USUARIOS (id, nombre, kogos) VALUES (?, ?, ?)", (user_id, name, 0))
        await db.commit()

async def get_random_porro():
    """
    Selects a random row from the PORROS table.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM PORROS ORDER BY RANDOM() LIMIT 1") as cursor:
            return await cursor.fetchone()
