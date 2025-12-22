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

async def get_user_inventory(discord_id: int):
    """
    Fetches user's inventory data (euros, kogos, cali packs).
    Returns a dictionary with the inventory items.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT euros, kogos, cali_park, cali_dx, cali_semsem FROM USUARIOS WHERE id = ?", (discord_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    'euros': row['euros'],
                    'kogos': row['kogos'],
                    'cali_park': row['cali_park'],
                    'cali_dx': row['cali_dx'],
                    'cali_semsem': row['cali_semsem']
                }
            return None

async def get_user_joints_paginated(discord_id: int, offset: int = 0, limit: int = 25):
    """
    Fetches user's owned joints with pagination.
    Returns list of tuples (joint_name, cantidad) and total count.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM RELACION_USUARIOS_PORROS WHERE id_user = ?"
        async with db.execute(count_query, (discord_id,)) as cursor:
            total_row = await cursor.fetchone()
            total = total_row['total'] if total_row else 0
        
        # Get paginated results
        query = """
        SELECT p.nombre, r.cantidad 
        FROM RELACION_USUARIOS_PORROS r
        JOIN PORROS p ON r.id_porro = p.id
        WHERE r.id_user = ?
        ORDER BY p.nombre
        LIMIT ? OFFSET ?
        """
        async with db.execute(query, (discord_id, limit, offset)) as cursor:
            rows = await cursor.fetchall()
            joints = [(row['nombre'], row['cantidad']) for row in rows]
            return joints, total

async def update_user_currency(discord_id: int, euros: int = 0, kogos: int = 0):
    """
    Updates user's euros and/or kogos by adding the specified amounts.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE USUARIOS SET euros = euros + ?, kogos = kogos + ? WHERE id = ?",
            (euros, kogos, discord_id)
        )
        await db.commit()

async def decrement_cali_pack(discord_id: int, pack_type: str):
    """
    Decrements the specified cali pack count for a user.
    pack_type should be one of: 'cali_park', 'cali_dx', 'cali_semsem'
    Returns True if successful, False if user doesn't have any packs.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if user has the pack
        async with db.execute(f"SELECT {pack_type} FROM USUARIOS WHERE id = ?", (discord_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] <= 0:
                return False
        
        # Decrement the pack
        await db.execute(
            f"UPDATE USUARIOS SET {pack_type} = {pack_type} - 1 WHERE id = ?",
            (discord_id,)
        )
        await db.commit()
        return True

async def get_random_joint_by_rarity(edition: str, rarity: int):
    """
    Selects a random joint from PORROS table matching edition and rarity.
    edition: 'PAR' for Park Bangers, 'SEM' for Sweet Semsem, 'DLX' for Deluxe
    rarity: 1 (common), 2 (rare), 3 (epic), 4 (legendary)
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM PORROS WHERE edicion = ? AND rareza = ? ORDER BY RANDOM() LIMIT 1",
            (edition, rarity)
        ) as cursor:
            return await cursor.fetchone()

async def get_user_cali_packs(discord_id: int):
    """
    Returns a dictionary of user's cali pack counts.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT cali_park, cali_dx, cali_semsem FROM USUARIOS WHERE id = ?",
            (discord_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    'cali_park': row['cali_park'],
                    'cali_dx': row['cali_dx'],
                    'cali_semsem': row['cali_semsem']
                }
            return None

async def update_user_cali_pack(discord_id: int, pack_type: str, amount: int):
    """
    Updates user's cali pack count by adding the specified amount.
    pack_type: 'cali_park', 'cali_dx', 'cali_semsem'
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE USUARIOS SET {pack_type} = {pack_type} + ? WHERE id = ?",
            (amount, discord_id)
        )
        await db.commit()

async def get_last_paga(discord_id: int):
    """
    Returns the last paga timestamp for a user.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT last_paga FROM USUARIOS WHERE id = ?", (discord_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def update_last_paga(discord_id: int, timestamp: str):
    """
    Updates the last paga timestamp for a user.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE USUARIOS SET last_paga = ? WHERE id = ?", (timestamp, discord_id))
        await db.commit()

async def get_user_balance(discord_id: int):
    """
    Returns the user's euro balance.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT euros FROM USUARIOS WHERE id = ?", (discord_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
