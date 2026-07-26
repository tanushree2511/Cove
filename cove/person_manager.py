import json
import os
from typing import Optional

from vision_config import CONFIG


class PersonManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or CONFIG.people_db_path
        self.people = self.load_db()

    def load_db(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                return json.load(f)
        return {}

    def save_people(self, clusters, valid_paths, overwrite=False):
        """
        Syncs clustering results to the DB.
        overwrite=True will WIPE the database clean before saving (Useful for tuning).
        """
        if overwrite:
            print("⚠️ Overwrite Mode: Clearing old database...")
            self.people = {}

        for i, label in enumerate(clusters):
            if label == -1: continue # Skip noise
            
            person_id = f"Person_{label}"
            
            # Create person if not exists
            if person_id not in self.people:
                self.people[person_id] = {"name": "Unknown", "photos": []}
            
            # Avoid duplicates
            if valid_paths[i] not in self.people[person_id]["photos"]:
                self.people[person_id]["photos"].append(valid_paths[i])
        
        # Save to disk
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w') as f:
            json.dump(self.people, f, indent=4)
        
        print(f"✅ People DB updated. Database now has {len(self.people)} unique people.")

    def rename_person(self, person_id, new_name):
        if person_id in self.people:
            self.people[person_id]["name"] = new_name
            with open(self.db_path, 'w') as f:
                json.dump(self.people, f, indent=4)
            print(f"👤 {person_id} is now known as {new_name}")