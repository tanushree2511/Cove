# watcher.py
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import requests

class NewImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(('.jpg', '.png', '.jpeg')):
            print(f"New file detected: {event.src_path}")
            # Notify the FastAPI server to index this specific file
            try:
                requests.post("http://localhost:8000/index/image", 
                              json={"file_path": event.src_path})
            except Exception as e:
                print(f"Failed to index: {e}")

def start_watching(path_to_watch):
    observer = Observer()
    event_handler = NewImageHandler()
    observer.schedule(event_handler, path_to_watch, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    watch_dir = sys.argv[1] if len(sys.argv) > 1 else "test_images"
    print(f"👁️ Watching '{watch_dir}' for new images...")
    start_watching(watch_dir)