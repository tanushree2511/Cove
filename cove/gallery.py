import os
import json
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

from vision_config import CONFIG

def generate_gallery():
    # 1. Load Data
    if not os.path.exists(CONFIG.people_db_path):
        print("❌ No database found.")
        return

    with open(CONFIG.people_db_path, "r") as f:
        people = json.load(f)

    print(f"Loaded {len(people)} clusters from database.")

    # 2. Build HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Vision Archive - Clusters</title>
        <style>
            body { background-color: #121212; color: #e0e0e0; font-family: sans-serif; padding: 20px; }
            h1 { text-align: center; color: #00e676; }
            .person-card { background: #1e1e1e; margin-bottom: 30px; padding: 20px; border-radius: 12px; }
            .person-header { border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; }
            .person-name { font-size: 1.2em; font-weight: bold; color: #fff; }
            .grid { display: flex; flex-wrap: wrap; gap: 10px; }
            .img-container { width: 100px; height: 100px; overflow: hidden; border-radius: 6px; }
            img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.2s; }
            img:hover { transform: scale(1.1); cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>👁️ VisionArchive Intelligence</h1>
    """

    # Sort by photo count
    sorted_people = sorted(people.items(), key=lambda x: len(x[1]['photos']), reverse=True)

    for person_id, data in sorted_people:
        if person_id == "Person_-1" or len(data['photos']) < 2:
            continue

        html += f"""
        <div class="person-card">
            <div class="person-header">
                <span class="person-name">{data['name']} ({len(data['photos'])} photos)</span>
            </div>
            <div class="grid">
        """
        
        # Show first 20 photos
        for full_path in data['photos'][:20]:
            # Use stored path (relative preferred, fall back for absolute)
            if os.path.isabs(full_path):
                filename = os.path.basename(full_path)
                relative_path = f"test_images/{filename}"
            else:
                relative_path = full_path
            filename = os.path.basename(full_path)
            
            html += f"""
                <div class="img-container">
                    <img src="{relative_path}" loading="lazy" alt="{filename}">
                </div>
            """
            
        html += "</div></div>"

    html += "</body></html>"

    with open("gallery.html", "w") as f:
        f.write(html)
    
    print("✅ Gallery generated: gallery.html")

def start_server():
    # Automatically start the server for you
    port = 8080
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"🚀 Server started! Open this link: http://localhost:{port}/gallery.html")
    print("   (Press Ctrl+C to stop)")
    webbrowser.open(f"http://localhost:{port}/gallery.html")
    httpd.serve_forever()

if __name__ == "__main__":
    generate_gallery()
    start_server()