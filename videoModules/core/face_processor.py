import cv2
import os
import uuid
import numpy as np
import json
import sqlite3
import torch
from insightface.app import FaceAnalysis
from scipy.spatial.distance import cosine
import hdbscan

# Lazy loading for Face Analysis
_face_app = None
FACES_DIR = "static/face_thumbnails"
os.makedirs(FACES_DIR, exist_ok=True)
DB_PATH = "data/videos.db"

def get_face_app():
    global _face_app
    if _face_app is None:
        # Check if we should use CPU or GPU
        # If CUDA is available but failing, we default to CPU
        providers = ['CPUExecutionProvider']
        if torch.cuda.is_available():
            # Try to use CUDA, but keep CPU as backup
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            
        print(f"DEBUG: Initializing FaceAnalysis with providers: {providers}")
        try:
            _face_app = FaceAnalysis(name='buffalo_l', providers=providers)
            _face_app.prepare(ctx_id=0, det_size=(320, 320))
        except Exception as e:
            print(f"DEBUG: CUDA failed, falling back to CPU. Error: {e}")
            _face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
            _face_app.prepare(ctx_id=-1, det_size=(320, 320))
            
    return _face_app

clustering_progress = {"current": 0, "total": 100, "message": "Idle"}

def get_known_people():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT person_id, embedding FROM faces GROUP BY person_id")
    data = cursor.fetchall()
    conn.close()
    return [(row[0], np.array(json.loads(row[1]))) for row in data]

def process_and_link_faces(frames, video_id):
    if not frames: return
    face_app = get_face_app()
    known_people = get_known_people()
    
    # Critical optimization: Only scan 1 frame (middle) for faces during bulk
    frame = frames[len(frames)//2]
    print(f"DEBUG: Detecting faces in 1 representative frame...")
    
    try:
        faces = face_app.get(frame)
        for face in faces:
            new_emb = face.normed_embedding
            matched_person_id = None
            for p_id, p_emb in known_people:
                score = cosine(new_emb, p_emb)
                if score < 0.45:
                    matched_person_id = p_id
                    break
            
            bbox = face.bbox.astype(int)
            y1, y2, x1, x2 = max(0, bbox[1]), bbox[3], max(0, bbox[0]), bbox[2]
            face_img = frame[y1:y2, x1:x2]
            thumb_name = f"{uuid.uuid4()}.jpg"
            if face_img.size > 0:
                cv2.imwrite(os.path.join(FACES_DIR, thumb_name), face_img)
            
            if matched_person_id is None:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("INSERT INTO persons (name, thumbnail) VALUES (?, ?)", (None, thumb_name))
                matched_person_id = cur.lastrowid
                conn.commit()
                conn.close()
                known_people.append((matched_person_id, new_emb))
            
            from core.database import link_face_to_person
            confidence = float(face.det_score) if hasattr(face, 'det_score') else 0.0
            link_face_to_person(video_id, matched_person_id, new_emb.tolist(), thumb_name, confidence)
    except Exception as e:
        print(f"DEBUG: Error in face detection: {e}")

def cluster_all_faces():
    global clustering_progress
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    clustering_progress = {"current": 10, "total": 100, "message": "Fetching face data..."}
    cursor.execute("SELECT f.id, f.embedding, f.thumbnail_path, p.name FROM faces f LEFT JOIN persons p ON f.person_id = p.id")
    rows = cursor.fetchall()
    if not rows: conn.close(); clustering_progress = {"current": 100, "total": 100, "message": "No faces found."}; return {"message": "No faces"}
    face_ids = [r[0] for r in rows]; embeddings = np.array([json.loads(r[1]) for r in rows])
    thumbnails = [r[2] for r in rows]; old_names = [r[3] for r in rows]
    clustering_progress = {"current": 30, "total": 100, "message": "Clustering faces..."}
    clusterer = hdbscan.HDBSCAN(min_cluster_size=2, metric='euclidean', cluster_selection_epsilon=0.5)
    labels = clusterer.fit_predict(embeddings)
    clustering_progress = {"current": 50, "total": 100, "message": "Updating identities..."}
    cursor.execute("DELETE FROM persons"); cursor.execute("DELETE FROM sqlite_sequence WHERE name='persons'")
    unique_labels = set(labels); new_person_map = {}
    for label in unique_labels:
        if label == -1: continue
        indices = [i for i, l in enumerate(labels) if l == label]
        cluster_names = [old_names[i] for i in indices if old_names[i] is not None]
        name = max(set(cluster_names), key=cluster_names.count) if cluster_names else None
        thumb = thumbnails[indices[0]]
        cursor.execute("INSERT INTO persons (name, thumbnail) VALUES (?, ?)", (name, thumb))
        new_person_map[label] = cursor.lastrowid
    total_faces = len(face_ids)
    for i, face_id in enumerate(face_ids):
        label = labels[i]
        new_p_id = new_person_map[label] if label != -1 else None
        if label == -1:
            cursor.execute("INSERT INTO persons (name, thumbnail) VALUES (?, ?)", (None, thumbnails[i]))
            new_p_id = cursor.lastrowid
        cursor.execute("UPDATE faces SET person_id = ? WHERE id = ?", (new_p_id, face_id))
        if i % 20 == 0: clustering_progress = {"current": 50 + int((i/total_faces) * 50), "total": 100, "message": f"Mapping: {i}/{total_faces}"}
    conn.commit(); conn.close(); clustering_progress = {"current": 100, "total": 100, "message": "Complete!"}
    return {"message": "Done", "clusters": len(new_person_map)}

def remove_duplicate_faces(video_id=None):
    conn = sqlite3.connect(DB_PATH); cursor = conn.cursor()
    query = "SELECT id, person_id, embedding, thumbnail_path FROM faces"
    if video_id: query += f" WHERE video_id = {video_id}"
    cursor.execute(query); rows = cursor.fetchall()
    if not rows: conn.close(); return 0
    to_delete = []; by_person = {}
    for r in rows: p_id = r[1]; by_person.setdefault(p_id, []).append(r)
    count = 0
    for p_id, p_faces in by_person.items():
        if len(p_faces) < 2: continue
        kept = []
        for f in p_faces:
            is_duplicate = False; emb = np.array(json.loads(f[2]))
            for k_f in kept:
                if cosine(emb, np.array(json.loads(k_f[2]))) < 0.05: is_duplicate = True; break
            if is_duplicate: to_delete.append(f[0]); count += 1; os.remove(os.path.join(FACES_DIR, f[3]))
            else: kept.append(f)
    if to_delete:
        for i in range(0, len(to_delete), 500):
            chunk = to_delete[i:i+500]
            cursor.execute(f"DELETE FROM faces WHERE id IN ({','.join(map(str, chunk))})")
    conn.commit(); conn.close(); return count