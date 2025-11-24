import aiosqlite
import os

DB_PATH = os.path.join("Databases", "darkmatter_pro.db")

async def add_user_porro(discord_id: int, id_porro: int):
    """
    Adds a joint to the user's collection or increments quantity if it exists.
    Uses discord_id directly as id_user.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if relation exists
        async with db.execute("SELECT cantidad FROM RELACION_USUARIOS_PORROS WHERE id_user = ? AND id_porro = ?", (discord_id, id_porro)) as cursor:
            row = await cursor.fetchone()

        if row:
            # Update quantity
            new_quantity = row[0] + 1
            await db.execute("UPDATE RELACION_USUARIOS_PORROS SET cantidad = ? WHERE id_user = ? AND id_porro = ?", (new_quantity, discord_id, id_porro))
        else:
            # Insert new row
            await db.execute("INSERT INTO RELACION_USUARIOS_PORROS (id_user, id_porro, cantidad) VALUES (?, ?, ?)", (discord_id, id_porro, 1))
        
        await db.commit()

async def get_porros_by_edition(edition: str):
    """
    Fetches all joints for a specific edition.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM PORROS WHERE edicion = ?", (edition,)) as cursor:
            return await cursor.fetchall()

async def get_user_porros(discord_id: int, edition: str):
    """
    Fetches all joints owned by a user for a specific edition.
    Returns a dictionary {id_porro: cantidad} for easier lookup.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        query = """
        SELECT p.id, r.cantidad 
        FROM RELACION_USUARIOS_PORROS r
        JOIN PORROS p ON r.id_porro = p.id
        WHERE r.id_user = ? AND p.edicion = ?
        """
        async with db.execute(query, (discord_id, edition)) as cursor:
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}
