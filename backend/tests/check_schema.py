import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "qc_tests.db"
print(f"Checking database at: {db_path}")
print(f"Database exists: {db_path.exists()}")

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get the CREATE TABLE statement
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='weekly_niveau_helium'")
    result = cursor.fetchone()

    if result:
        print("\nCurrent schema for weekly_niveau_helium:")
        print(result[0])
    else:
        print("\nTable 'weekly_niveau_helium' not found in database")
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print(f"\nAll tables ({len(tables)}):")
    for table in tables:
        print(f"  - {table[0]}")

    conn.close()
else:
    print("Database file does not exist!")
