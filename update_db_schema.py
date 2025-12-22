import sqlite3
import os

db_path = r"Databases/darkmatter_pro.db"

def update_schema():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add last_paga column to USUARIOS table if it doesn't exist
        try:
            cursor.execute("ALTER TABLE USUARIOS ADD COLUMN last_paga TEXT DEFAULT NULL")
            print("Added column last_paga to USUARIOS")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column last_paga already exists in USUARIOS")
            else:
                raise e
        
        conn.commit()
        conn.close()
        print("Database updated successfully.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_schema()
