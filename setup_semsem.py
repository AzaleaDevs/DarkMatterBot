import aiosqlite
import asyncio
import os
import random

DB_PATH = os.path.join("Databases", "darkmatter_pro.db")

async def setup_semsem():
    print("Iniciando setup de Sweet Semsem...")
    
    async with aiosqlite.connect(DB_PATH) as db:
        # Check current count
        async with db.execute("SELECT COUNT(*) FROM PORROS WHERE edicion = 'SEM'") as cursor:
            count = await cursor.fetchone()
            print(f"Items actuales de SEM: {count[0]}")

        # Insert items 26-50
        print("Insertando items...")
        for i in range(26, 51):
            # Check if exists
            async with db.execute("SELECT id FROM PORROS WHERE id = ?", (i,)) as cursor:
                if await cursor.fetchone():
                    print(f"Item {i} ya existe. Saltando.")
                    continue
            
            # Roll rarity
            roll = random.random() * 100
            if roll < 48:
                rarity = 1  # Common
            elif roll < 72:
                rarity = 2  # Rare
            elif roll < 88:
                rarity = 3  # Epic
            else:
                rarity = 4  # Legendary

            name = f"Sweet Semsem #{i}"
            description = "Un porro dulce y suave."
            edition = "SEM"
            
            await db.execute(
                "INSERT INTO PORROS (id, nombre, descripcion, edicion, rareza) VALUES (?, ?, ?, ?, ?)",
                (i, name, description, edition, rarity)
            )
            print(f"Insertado {name} (Rareza: {rarity})")
        
        await db.commit()
    print("Setup completado.")

if __name__ == "__main__":
    asyncio.run(setup_semsem())
