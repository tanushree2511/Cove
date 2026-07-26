import subprocess
import time
import shutil
import os
import requests
import sys
import signal

# Configuration
SERVER_PORT = 8000
WATCH_DIR = "test_images"
# Pick a source image that exists
SOURCE_IMAGE = "test_images/Zinedine_Zidane_0001.jpg"
TARGET_IMAGE = "test_images/live_test_zidane.jpg"

def cleanup(processes):
    print("\n[TEST] Cleaning up...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
            p.wait()
    
    if os.path.exists(TARGET_IMAGE):
        os.remove(TARGET_IMAGE)
    print("[TEST] Cleanup complete.")

def run_integration_test():
    processes = []
    try:
        # 1. Start Server
        print("[TEST] Starting Server (server.py)...")
        server_process = subprocess.Popen(
            [sys.executable, "server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(server_process)
        
        # Wait for server to be ready
        print("[TEST] Waiting for server to initialize (this make take a moment for AI models)...")
        server_ready = False
        for i in range(60): # Wait up to 60 seconds (model loading issues)
            try:
                # Try a lightweight request to checking if it accepts connections
                response = requests.post(f"http://localhost:{SERVER_PORT}/search/text", 
                                       json={"text": "ping", "limit": 1})
                if response.status_code == 200:
                    server_ready = True
                    print("[TEST] Server is UP!")
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(1)
            
        if not server_ready:
            print("[TEST] Server failed to start within timeout.")
            print("Server Stderr:", server_process.stderr.read())
            return

        # 2. Start Watcher
        print("[TEST] Starting Watcher (watcher.py)...")
        # Watcher needs to know which directory to watch. 
        # Looking at watcher.py, it likely takes an arg or has a default.
        # Let's assume we pass the dir as an arg based on standard practice, 
        # OR we check how it's implemented. 
        # Wait, I didn't verify if watcher.py takes an ARG.
        # checking watcher.py...
        watcher_process = subprocess.Popen(
            [sys.executable, "watcher.py", WATCH_DIR],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        processes.append(watcher_process)
        time.sleep(2) # Give watcher a moment

        # 3. Simulate New File
        print(f"[TEST] Simulating new file creation: copying {SOURCE_IMAGE} -> {TARGET_IMAGE}")
        if not os.path.exists(SOURCE_IMAGE):
            print(f"[TEST] ERROR: Source image {SOURCE_IMAGE} not found. Cannot proceed.")
            # List valid files
            print("Files in test_images:", os.listdir("test_images")[:5])
            return

        shutil.copy(SOURCE_IMAGE, TARGET_IMAGE)
        
        # 4. Wait for processing
        print("[TEST] Waiting for processing (5 seconds)...")
        time.sleep(5)
        
        # 5. Verify Indexing
        print("[TEST] Verifying indexing via Search API...")
        # Search for "Zidane" or generic "man" if we don't have text search model fully fine tuned, 
        # but since we indexed it, the vector storage should have it.
        # Actually our search engine uses text-to-image.
        # Let's try searching for "Zidane"
        query = "Zinedine Zidane"
        response = requests.post(f"http://localhost:{SERVER_PORT}/search/text", 
                               json={"text": query, "limit": 5})
        
        if response.status_code == 200:
            results = response.json().get("results", [])
            print(f"[TEST] Search Results for '{query}': {results}")
            
            # Check if our new file is in there
            found = False
            for res in results:
                if "live_test_zidane.jpg" in res.get("path", ""):
                    found = True
                    break
            
            if found:
                print("\n[TEST] SUCCESS: The new image was indexed and found via search!")
            else:
                print("\n[TEST] FAILURE: Image not found in search results.")
        else:
             print(f"[TEST] FAILURE: Search API returned {response.status_code}")
             print(response.text)

    except Exception as e:
        print(f"[TEST] Exception: {e}")
    finally:
        cleanup(processes)

if __name__ == "__main__":
    run_integration_test()
