"""
Add results_json column to weekly_piqt table
Run this to update existing databases
"""
import sqlite3
import os

# Use the correct database path from config
db_path = os.path.join(os.path.dirname(__file__), 'data', 'qc_tests.db')

print(f"Updating database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Add results_json column to weekly_piqt
    cursor.execute("ALTER TABLE weekly_piqt ADD COLUMN results_json TEXT")
    conn.commit()
    print("✅ Added results_json column to weekly_piqt table")
except sqlite3.OperationalError as e:
    if "duplicate column" in str(e).lower():
        print("⚠️  Column results_json already exists")
    else:
        print(f"❌ Error: {e}")
finally:
    conn.close()

print("\n✅ Database migration complete!")
print("\nNow update the save endpoint to store results as JSON:")
print("  1. The frontend sends 'results' array in the POST data")
print("  2. The backend converts it to JSON: json.dumps(data.get('results', []))")
print("  3. Pass it as results_json=... to save_generic_test_to_database()")
