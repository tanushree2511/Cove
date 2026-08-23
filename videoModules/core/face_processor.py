import sys
import logging
import cv2
import os
import uuid
import numpy as np
import json
import sqlite3

from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../cove')))
try:
    from config.vision_config import CONFIG
    BASE_DATA_DIR = CONFIG.user_data_dir
except Exception:
    try:
        from cove.config.vision_config import CONFIG
        BASE_DATA_DIR = CONFIG.user_data_dir
    except Exception:
        BASE_DATA_DIR = os.getcwd()

from core.database import DB_PATH

# Lazy loading for Face Analysis
_face_app = None
FACES_DIR = os.path.join(BASE_DATA_DIR, "static", "face_thumbnails")
os.makedirs(FACES_DIR, exist_ok=True)

def get_face_app():
    global _face_app
    if _face_app is None:
        logger.info("Initializing FaceAnalysis with providers: %s, root: %s", CONFIG.providers, CONFIG.assets_base)
        _face_app = FaceAnalysis(
            name='buffalo_s',
            root=CONFIG.assets_base,
            allowed_modules=['detection', 'recognition'],
            providers=CONFIG.providers
        )
        det_size = (320, 320) if not CONFIG.use_gpu else (640, 640)
        _face_app.prepare(ctx_id=CONFIG.ctx_id, det_size=det_size)
    return _face_app

clustering_progress = {"current": 0, "total": 100, "message": "Idle"}

def get_known_people():
    """
    Returns a dict mapping person_id -> list of normalized numpy embeddings.
    Allows multi-exemplar matching against all angles/expressions of a person.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT person_id, embedding FROM faces WHERE person_id IS NOT NULL")
    data = cursor.fetchall()
    conn.close()

    person_embeddings = {}
    for p_id, emb_json in data:
        try:
            emb = np.array(json.loads(emb_json), dtype=np.float32)
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
                person_embeddings.setdefault(p_id, []).append(emb)
        except Exception:
            pass
    return person_embeddings

def process_and_link_faces(frames, video_id):
    if not frames:
        return
    face_app = get_face_app()
    known_people = get_known_people()

    logger.info(f"DEBUG: Detecting faces in all {len(frames)} representative frames for video {video_id}...")

    detected_person_ids = set()

    for f_idx, frame in enumerate(frames):
        try:
            faces = face_app.get(frame)
            if not faces:
                continue

            for face in faces:
                # 1. Skip low-confidence false positives
                if hasattr(face, 'det_score') and face.det_score < 0.35:
                    continue

                # 2. Skip extreme side-view / back-of-head angles
                pose_yaw = float(face.pose[1]) if hasattr(face, 'pose') and face.pose is not None else None
                if pose_yaw is not None and abs(pose_yaw) > 75.0:
                    continue

                bbox = face.bbox.astype(int)
                y1, y2, x1, x2 = max(0, bbox[1]), max(0, bbox[3]), max(0, bbox[0]), max(0, bbox[2])
                face_w, face_h = (x2 - x1), (y2 - y1)

                # 3. Skip tiny distant faces (< 24x24 px)
                if face_w * face_h < 576:
                    continue

                face_img = frame[y1:y2, x1:x2]
                if face_img.size == 0:
                    continue

                # 4. Skip blurry faces using Laplacian variance
                gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
                blur_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
                if blur_var < 10.0:
                    continue

                new_emb = np.array(face.normed_embedding, dtype=np.float32)
                norm = np.linalg.norm(new_emb)
                if norm > 0:
                    new_emb = new_emb / norm

                matched_person_id = None
                best_similarity = -1.0

                # Multi-exemplar matching: compare against all face embeddings stored for known people
                for p_id, emb_list in known_people.items():
                    sims = [float(np.dot(new_emb, p_emb)) for p_emb in emb_list]
                    max_sim = max(sims) if sims else -1.0
                    if max_sim > best_similarity:
                        best_similarity = max_sim
                        matched_person_id = p_id

                # Match threshold: Cosine similarity >= 0.32 for video frames (accounting for motion/sunglasses/lighting)
                if best_similarity >= 0.32 and matched_person_id is not None:
                    # Link to existing person
                    known_people[matched_person_id].append(new_emb)
                else:
                    matched_person_id = None

                # Don't duplicate linking the same person multiple times in the same video run
                if matched_person_id is not None and matched_person_id in detected_person_ids:
                    continue

                thumb_name = f"{uuid.uuid4()}.jpg"
                cv2.imwrite(os.path.join(FACES_DIR, thumb_name), face_img)

                if matched_person_id is None:
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    cur.execute("INSERT INTO persons (name, thumbnail) VALUES (?, ?)", (None, thumb_name))
                    matched_person_id = cur.lastrowid
                    conn.commit()
                    conn.close()
                    known_people.setdefault(matched_person_id, []).append(new_emb)

                detected_person_ids.add(matched_person_id)

                from core.database import link_face_to_person
                confidence = float(face.det_score) if hasattr(face, 'det_score') else 0.0
                link_face_to_person(video_id, matched_person_id, new_emb.tolist(), thumb_name, confidence, pose_yaw)
                logger.info(f"DEBUG: Linked face in video {video_id} -> person {matched_person_id} (sim={best_similarity:.2f}, conf={confidence:.2f})")
        except Exception as e:
            logger.exception(f"DEBUG: Error in face detection on frame {f_idx}: {e}")

def cluster_all_faces():
    """
    Groups all face embeddings into distinct person identities using graph-based cosine similarity clustering.
    Merges duplicate detections of the same person across frames and videos.
    """
    global clustering_progress
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    clustering_progress = {"current": 10, "total": 100, "message": "Fetching face database..."}
    cursor.execute("SELECT f.id, f.embedding, f.thumbnail_path, p.name, f.confidence, f.pose_yaw FROM faces f LEFT JOIN persons p ON f.person_id = p.id")
    rows = cursor.fetchall()
    if not rows:
        conn.close()
        clustering_progress = {"current": 100, "total": 100, "message": "No faces in database."}
        return {"message": "No faces", "clusters": 0}
    
    face_ids = [r[0] for r in rows]
    raw_embeddings = [np.array(json.loads(r[1]), dtype=np.float32) for r in rows]
    thumbnails = [r[2] for r in rows]
    old_names = [r[3] for r in rows]
    confidences = [r[4] or 0.0 for r in rows]
    yaws = [r[5] or 0.0 for r in rows]

    # Normalize vectors
    embeddings = []
    for emb in raw_embeddings:
        norm = np.linalg.norm(emb)
        embeddings.append(emb / norm if norm > 0 else emb)
    embeddings = np.array(embeddings)

    clustering_progress = {"current": 30, "total": 100, "message": "Clustering identities with cosine similarity..."}

    # Graph Connected Components with 0.31 Cosine Similarity Threshold
    threshold = 0.31
    n = len(embeddings)
    adj = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            sim = float(np.dot(embeddings[i], embeddings[j]))
            if sim >= threshold:
                adj[i].add(j)
                adj[j].add(i)

    visited = set()
    clusters = []
    for i in range(n):
        if i not in visited:
            comp = []
            queue = [i]
            visited.add(i)
            while queue:
                node = queue.pop(0)
                comp.append(node)
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            clusters.append(comp)

    clustering_progress = {"current": 60, "total": 100, "message": "Updating database records..."}
    cursor.execute("DELETE FROM persons")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='persons'")

    new_person_map = {}
    for cluster_id, member_indices in enumerate(clusters):
        cluster_names = [old_names[idx] for idx in member_indices if old_names[idx] is not None]
        name = max(set(cluster_names), key=cluster_names.count) if cluster_names else None
        
        # Pick the best thumbnail (highest confidence, lowest yaw)
        best_thumb_idx = member_indices[0]
        best_score = -1.0
        for idx in member_indices:
            score = confidences[idx] - (abs(yaws[idx]) / 180.0) * 0.2
            if score > best_score:
                best_score = score
                best_thumb_idx = idx
                
        thumb = thumbnails[best_thumb_idx]
        cursor.execute("INSERT INTO persons (name, thumbnail) VALUES (?, ?)", (name, thumb))
        new_person_id = cursor.lastrowid
        
        for idx in member_indices:
            cursor.execute("UPDATE faces SET person_id = ? WHERE id = ?", (new_person_id, face_ids[idx]))

    conn.commit()
    conn.close()
    clustering_progress = {"current": 100, "total": 100, "message": f"Merged into {len(clusters)} distinct people."}
    return {"message": "Done", "clusters": len(clusters)}

def remove_duplicate_faces(video_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT id, person_id, embedding, thumbnail_path FROM faces"
    if video_id:
        query += f" WHERE video_id = {video_id}"
    cursor.execute(query)
    rows = cursor.fetchall()
    if not rows:
        conn.close()
        return 0
        
    to_delete = []
    by_person = {}
    for r in rows:
        p_id = r[1]
        by_person.setdefault(p_id, []).append(r)
        
    count = 0
    for p_id, p_faces in by_person.items():
        if len(p_faces) < 2:
            continue
        kept = []
        for f in p_faces:
            is_duplicate = False
            emb = np.array(json.loads(f[2]), dtype=np.float32)
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            for k_f in kept:
                k_emb = np.array(json.loads(k_f[2]), dtype=np.float32)
                k_norm = np.linalg.norm(k_emb)
                if k_norm > 0:
                    k_emb = k_emb / k_norm
                if float(np.dot(emb, k_emb)) > 0.90:
                    is_duplicate = True
                    break
            if is_duplicate:
                to_delete.append(f[0])
                count += 1
                try:
                    os.remove(os.path.join(FACES_DIR, f[3]))
                except Exception:
                    pass
            else:
                kept.append(f)
                
    if to_delete:
        for i in range(0, len(to_delete), 500):
            chunk = to_delete[i:i + 500]
            cursor.execute(f"DELETE FROM faces WHERE id IN ({','.join(map(str, chunk))})")
    conn.commit()
    conn.close()
    return count
