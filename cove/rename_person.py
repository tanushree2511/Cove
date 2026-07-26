import json
import os
import sys

from vision_config import CONFIG


def main():
    db_path = CONFIG.people_db_path
    
    if len(sys.argv) < 3:
        print("Usage: python rename_person.py <Person_ID> <New Name>")
        print("Example: python rename_person.py Person_0 \"Aaron Peirsol\"")
        return

    target_id = sys.argv[1]
    new_name = sys.argv[2]

    if not os.path.exists(db_path):
        print("❌ DB not found.")
        return

    with open(db_path, "r") as f:
        data = json.load(f)

    if target_id not in data:
        print(f"❌ Error: '{target_id}' does not exist in the database.")
        print("Check gallery.html for the correct ID (e.g., Person_5).")
        return

    # Update Name
    old_name = data[target_id]['name']
    data[target_id]['name'] = new_name
    
    # Save
    with open(db_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Success: '{old_name}' ({target_id}) is now '{new_name}'")

if __name__ == "__main__":
    main()