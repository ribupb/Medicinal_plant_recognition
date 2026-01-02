import sqlite3
import json

# File names
DB_NAME = "plants.db"
JSON_FILE = "D:\\Project trial\\Medicinal_plant_recognition\\static\\plant_info.json"

# 1. Connect to SQLite (creates file if not exists)
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# 2. Create plants table
cursor.execute("""
CREATE TABLE IF NOT EXISTS plants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    scientific_name TEXT,
    description TEXT,
    medicinal_uses TEXT,
    region TEXT,
    image_url TEXT
)
""")

# 3. Load JSON data
with open(JSON_FILE, "r", encoding="utf-8") as f:
    plants_data = json.load(f)

# 4. Insert each plant
for plant in plants_data:
    # Join uses list into a single string
    uses_text = "\n".join(plant.get("uses", []))

    cursor.execute("""
        INSERT INTO plants (name, scientific_name, description, medicinal_uses, region, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        plant.get("name"),
        plant.get("scientific_name"),
        plant.get("description"),
        uses_text,
        plant.get("region"),
        plant.get("image")
    ))

# 5. Save changes
conn.commit()
conn.close()

print(f"✅ Migrated {len(plants_data)} plants from {JSON_FILE} → {DB_NAME}")
