import sqlite3
import os

db_path = r"Databases/darkmatter_pro.db"

def recreate_table():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop existing table
        cursor.execute("DROP TABLE IF EXISTS RELACION_USUARIOS_PORROS")
        print("Dropped table RELACION_USUARIOS_PORROS")
        
        # Create new table
        # id_user: Discord User ID (as requested)
        # id_porro: ID of the joint from PORROS table
        # cantidad: Quantity owned
        create_query = """
        CREATE TABLE RELACION_USUARIOS_PORROS (
            id_user INTEGER,
            id_porro INTEGER,
            cantidad INTEGER DEFAULT 1,
            PRIMARY KEY (id_user, id_porro)
        )
        """
        cursor.execute(create_query)
        print("Created table RELACION_USUARIOS_PORROS")
        
        conn.commit()
        conn.close()
        print("Database updated successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    recreate_table()
