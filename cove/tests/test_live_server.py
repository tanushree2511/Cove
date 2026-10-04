import requests
import os
import time

SERVER_URL = "http://127.0.0.1:8000"
TEST_IMAGE = "test_images/Zinedine_Zidane_0001.jpg"

def test_index_image():
    print(f"\n[INFO] Testing /index/image with {TEST_IMAGE}...")
    abs_path = os.path.abspath(TEST_IMAGE)
    
    if not os.path.exists(abs_path):
        print(f"[ERROR] Test image not found at {abs_path}")
        return False

    payload = {"file_path": abs_path}
    try:
        response = requests.post(f"{SERVER_URL}/index/image", json=payload)
        if response.status_code == 200:
            print("[SUCCESS] Image indexed successfully:")
            print(response.json())
            return True
        else:
            print(f"[FAIL] Server returned {response.status_code}:")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("[FAIL] Could not connect to server. Is it running?")
        return False

def test_search_text():
    print("\n[INFO] Testing /search/text with query 'football player'...")
    payload = {"text": "football player", "limit": 3}
    
    try:
        response = requests.post(f"{SERVER_URL}/search/text", json=payload)
        if response.status_code == 200:
            print("[SUCCESS] Search successful:")
            results = response.json().get("results", [])
            for r in results:
                print(f" - {r}")
            return True
        else:
            print(f"[FAIL] Server returned {response.status_code}:")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("[FAIL] Could not connect to server. Is it running?")
        return False

if __name__ == "__main__":
    print("--- Vision AI Engine Live Test ---")
    if test_index_image():
        time.sleep(1) # Give it a moment to save/process if async (though our server is sync for now)
        test_search_text()
