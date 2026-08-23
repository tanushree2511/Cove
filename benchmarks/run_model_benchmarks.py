"""
VisionArchive AI — Comprehensive Quantitative Model Evaluation and Benchmarking Suite.
Runs rigorous scientific evaluations on:
1. CLIP Cross-Modal Text & Image Embedding Engine
2. SCRFD Face Detection & ArcFace Feature Verification (ROC/AUC/EER)
3. Graph Connected Components Face Clustering (ARI/AMI/V-Measure)
4. Temporal Multi-Frame Video Representation & Classification
5. FAISS Vector Database Search Scaling & Latency Profiling
"""

import os
import sys
import time
import json
import glob
import re
import numpy as np
import sqlite3
from collections import defaultdict
from sklearn.metrics import roc_curve, auc, adjusted_rand_score, adjusted_mutual_info_score, homogeneity_completeness_v_measure

# Ensure project directories are in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "cove"))
sys.path.insert(0, os.path.join(BASE_DIR, "videoModules"))

from config.vision_config import CONFIG
from engines.search_engine import SearchEngine
from engines.vector_storage import VectorStorage
from core.face_processor import get_face_app
from core.embedder import generate_video_embedding, encode_text
from core.video_processor import extract_frames
from core.classifier import classify_video, LABEL_DEFINITIONS
import faiss

def get_system_specs():
    import platform
    import psutil
    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu": platform.processor() or "x86_64",
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "python_version": platform.python_version(),
        "providers": CONFIG.providers,
    }

def benchmark_clip():
    print("\n" + "="*70)
    print(" [1/5] BENCHMARKING CLIP EMBEDDING ENGINE (ViT-B/32)")
    print("="*70)

    engine = SearchEngine()
    test_img_dir = os.path.join(BASE_DIR, "cove", "test_images")
    img_files = sorted(glob.glob(os.path.join(test_img_dir, "*.jpg")))[:30]

    # 1. Text Latency
    test_queries = [
        "a portrait photo of a smiling man",
        "a woman with glasses and dark hair",
        "nature landscape with blue sky and trees",
        "busy city street traffic in daylight",
        "an athlete running outdoors in a stadium",
    ]
    text_latencies = []
    for _ in range(5):
        for q in test_queries:
            t0 = time.perf_counter()
            _ = engine.get_text_embedding(q)
            text_latencies.append((time.perf_counter() - t0) * 1000)
    
    avg_text_lat = np.mean(text_latencies)
    std_text_lat = np.std(text_latencies)
    print(f"  • Text Encoding Latency : {avg_text_lat:.2f} ± {std_text_lat:.2f} ms / query (N={len(text_latencies)})")

    # 2. Image Latency
    img_latencies = []
    img_embeddings = []
    for img_p in img_files:
        t0 = time.perf_counter()
        emb = engine.get_image_embedding(img_p)
        img_latencies.append((time.perf_counter() - t0) * 1000)
        if emb is not None:
            norm = np.linalg.norm(emb)
            img_embeddings.append((img_p, emb / norm if norm > 0 else emb))

    avg_img_lat = np.mean(img_latencies)
    std_img_lat = np.std(img_latencies)
    img_fps = 1000.0 / avg_img_lat if avg_img_lat > 0 else 0
    print(f"  • Image Encoding Latency: {avg_img_lat:.2f} ± {std_img_lat:.2f} ms / image ({img_fps:.1f} FPS)")

    # 3. Cross-Modal Text-to-Image Matching Precision
    correct_top1 = 0
    correct_top5 = 0
    mrr_total = 0.0
    evaluated_count = min(len(img_embeddings), 25)

    for i in range(evaluated_count):
        path, target_emb = img_embeddings[i]
        basename = os.path.basename(path)
        name_clean = " ".join(re.sub(r"_\d+\.jpg$", "", basename).split("_"))
        query = f"a photo of {name_clean}"
        q_emb = engine.get_text_embedding(query)
        q_norm = np.linalg.norm(q_emb)
        if q_norm > 0:
            q_emb = q_emb / q_norm

        sims = [float(np.dot(q_emb, cand_emb)) for _, cand_emb in img_embeddings]
        ranked_indices = np.argsort(sims)[::-1]
        
        rank = list(ranked_indices).index(i) + 1
        if rank == 1:
            correct_top1 += 1
        if rank <= 5:
            correct_top5 += 1
        mrr_total += 1.0 / rank

    r_at_1 = (correct_top1 / evaluated_count) * 100
    r_at_5 = (correct_top5 / evaluated_count) * 100
    mrr = (mrr_total / evaluated_count)

    print(f"  • Cross-Modal Recall@1 : {r_at_1:.1f}% ({correct_top1}/{evaluated_count})")
    print(f"  • Cross-Modal Recall@5 : {r_at_5:.1f}% ({correct_top5}/{evaluated_count})")
    print(f"  • Mean Reciprocal Rank  : {mrr:.4f}")

    return {
        "text_latency_ms": round(avg_text_lat, 2),
        "text_latency_std_ms": round(std_text_lat, 2),
        "image_latency_ms": round(avg_img_lat, 2),
        "image_latency_std_ms": round(std_img_lat, 2),
        "image_fps": round(img_fps, 2),
        "recall_at_1_percent": round(r_at_1, 2),
        "recall_at_5_percent": round(r_at_5, 2),
        "mrr": round(mrr, 4),
    }

def benchmark_face_verification():
    print("\n" + "="*70)
    print(" [2/5] BENCHMARKING FACE RECOGNITION (SCRFD + ArcFace 512-D)")
    print("="*70)

    face_app = get_face_app()
    test_img_dir = os.path.join(BASE_DIR, "cove", "test_images")
    all_imgs = sorted(glob.glob(os.path.join(test_img_dir, "*.jpg")))

    person_to_imgs = defaultdict(list)
    for p in all_imgs:
        fn = os.path.basename(p)
        person_name = re.sub(r"_\d+\.jpg$", "", fn)
        person_to_imgs[person_name].append(p)

    multi_img_persons = {k: v for k, v in person_to_imgs.items() if len(v) >= 2}
    print(f"  • Loaded {len(all_imgs)} LFW images across {len(person_to_imgs)} identities ({len(multi_img_persons)} multi-sample identities).")

    import cv2
    det_latencies = []
    person_embeddings = defaultdict(list)
    all_detected_faces = []

    for p_name, img_paths in multi_img_persons.items():
        for p in img_paths:
            img = cv2.imread(p)
            if img is None:
                continue
            t0 = time.perf_counter()
            faces = face_app.get(img)
            det_latencies.append((time.perf_counter() - t0) * 1000)
            if faces:
                best_face = max(faces, key=lambda f: f.det_score if hasattr(f, 'det_score') else 0.0)
                emb = np.array(best_face.normed_embedding, dtype=np.float32)
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                    person_embeddings[p_name].append(emb)
                    all_detected_faces.append((p_name, emb))

    avg_det_lat = np.mean(det_latencies) if det_latencies else 0.0
    print(f"  • Face Detection + Extraction Latency: {avg_det_lat:.2f} ms / image (RetinaFace/SCRFD + ArcFace)")

    pos_pairs = []
    neg_pairs = []

    p_names = list(person_embeddings.keys())
    for p_name, embs in person_embeddings.items():
        for i in range(len(embs)):
            for j in range(i + 1, len(embs)):
                sim = float(np.dot(embs[i], embs[j]))
                pos_pairs.append(sim)

    for i in range(len(p_names)):
        for j in range(i + 1, min(i + 10, len(p_names))):
            embs_a = person_embeddings[p_names[i]]
            embs_b = person_embeddings[p_names[j]]
            for ea in embs_a[:2]:
                for eb in embs_b[:2]:
                    sim = float(np.dot(ea, eb))
                    neg_pairs.append(sim)

    pos_mean = np.mean(pos_pairs) if pos_pairs else 0.0
    pos_std = np.std(pos_pairs) if pos_pairs else 0.0
    neg_mean = np.mean(neg_pairs) if neg_pairs else 0.0
    neg_std = np.std(neg_pairs) if neg_pairs else 0.0
    separation_margin = pos_mean - neg_mean

    print(f"  • Positive (Intra-Person) Similarity : {pos_mean:.3f} ± {pos_std:.3f} (N={len(pos_pairs)})")
    print(f"  • Negative (Inter-Person) Similarity : {neg_mean:.3f} ± {neg_std:.3f} (N={len(neg_pairs)})")
    print(f"  • Cosine Separation Margin            : +{separation_margin:.3f}")

    labels = np.array([1]*len(pos_pairs) + [0]*len(neg_pairs))
    scores = np.array(pos_pairs + neg_pairs)
    fpr, tpr, thresholds = roc_curve(labels, scores)
    roc_auc = auc(fpr, tpr)

    fnr = 1 - tpr
    eer_idx = np.nanargmin(np.absolute((fnr - fpr)))
    eer = (fpr[eer_idx] + fnr[eer_idx]) / 2.0
    optimal_threshold = thresholds[eer_idx]

    tau_target = 0.32
    far_at_tau = np.mean([s >= tau_target for s in neg_pairs]) * 100 if neg_pairs else 0.0
    frr_at_tau = np.mean([s < tau_target for s in pos_pairs]) * 100 if pos_pairs else 0.0
    acc_at_tau = 100.0 - (far_at_tau * len(neg_pairs) + frr_at_tau * len(pos_pairs)) / (len(neg_pairs) + len(pos_pairs))

    print(f"  • Area Under ROC Curve (AUC-ROC)     : {roc_auc:.4f}")
    print(f"  • Equal Error Rate (EER)             : {eer*100:.2f}% at threshold tau={optimal_threshold:.3f}")
    print(f"  • Verification Accuracy at tau=0.32   : {acc_at_tau:.2f}% (FAR={far_at_tau:.2f}%, FRR={frr_at_tau:.2f}%)")

    return {
        "face_detection_latency_ms": round(avg_det_lat, 2),
        "intra_person_similarity_mean": round(pos_mean, 4),
        "intra_person_similarity_std": round(pos_std, 4),
        "inter_person_similarity_mean": round(neg_mean, 4),
        "inter_person_similarity_std": round(neg_std, 4),
        "separation_margin": round(separation_margin, 4),
        "auc_roc": round(roc_auc, 4),
        "eer_percent": round(eer * 100, 2),
        "optimal_threshold": round(float(optimal_threshold), 4),
        "accuracy_at_032_percent": round(acc_at_tau, 2),
        "far_at_032_percent": round(far_at_tau, 2),
        "frr_at_032_percent": round(frr_at_tau, 2),
    }

def benchmark_clustering():
    print("\n" + "="*70)
    print(" [3/5] BENCHMARKING GRAPH CONNECTED-COMPONENTS FACE CLUSTERING")
    print("="*70)

    face_app = get_face_app()
    test_img_dir = os.path.join(BASE_DIR, "cove", "test_images")
    all_imgs = sorted(glob.glob(os.path.join(test_img_dir, "*.jpg")))[:60]

    ground_truth_labels = []
    face_embeddings = []
    import cv2

    for p in all_imgs:
        fn = os.path.basename(p)
        person_name = re.sub(r"_\d+\.jpg$", "", fn)
        img = cv2.imread(p)
        if img is None:
            continue
        faces = face_app.get(img)
        if faces:
            best_face = max(faces, key=lambda f: f.det_score if hasattr(f, 'det_score') else 0.0)
            emb = np.array(best_face.normed_embedding, dtype=np.float32)
            norm = np.linalg.norm(emb)
            if norm > 0:
                face_embeddings.append(emb / norm)
                ground_truth_labels.append(person_name)

    n = len(face_embeddings)
    print(f"  • Clustering {n} detected faces across {len(set(ground_truth_labels))} ground-truth identities...")

    threshold = 0.32
    adj = {i: set() for i in range(n)}
    for i in range(n):
        for j in range(i + 1, n):
            sim = float(np.dot(face_embeddings[i], face_embeddings[j]))
            if sim >= threshold:
                adj[i].add(j)
                adj[j].add(i)

    visited = set()
    predicted_cluster_ids = [-1] * n
    current_cluster = 0
    for i in range(n):
        if i not in visited:
            queue = [i]
            visited.add(i)
            while queue:
                node = queue.pop(0)
                predicted_cluster_ids[node] = current_cluster
                for neighbor in adj[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            current_cluster += 1

    ari = adjusted_rand_score(ground_truth_labels, predicted_cluster_ids)
    ami = adjusted_mutual_info_score(ground_truth_labels, predicted_cluster_ids)
    homo, compl, v_measure = homogeneity_completeness_v_measure(ground_truth_labels, predicted_cluster_ids)

    correct_members = 0
    for c_id in range(current_cluster):
        members = [ground_truth_labels[idx] for idx in range(n) if predicted_cluster_ids[idx] == c_id]
        if members:
            most_freq = max(set(members), key=members.count)
            correct_members += members.count(most_freq)
    purity = (correct_members / n) * 100 if n > 0 else 0.0

    print(f"  • Generated Clusters          : {current_cluster} (Ground Truth: {len(set(ground_truth_labels))})")
    print(f"  • Cluster Purity              : {purity:.2f}%")
    print(f"  • Adjusted Rand Index (ARI)   : {ari:.4f}")
    print(f"  • Adjusted Mutual Info (AMI)  : {ami:.4f}")
    print(f"  • Homogeneity Score           : {homo:.4f}")
    print(f"  • Completeness Score          : {compl:.4f}")
    print(f"  • V-Measure Score             : {v_measure:.4f}")

    return {
        "num_faces": n,
        "ground_truth_identities": len(set(ground_truth_labels)),
        "predicted_clusters": current_cluster,
        "purity_percent": round(purity, 2),
        "ari": round(ari, 4),
        "ami": round(ami, 4),
        "homogeneity": round(homo, 4),
        "completeness": round(compl, 4),
        "v_measure": round(v_measure, 4),
    }

def benchmark_video_pipeline():
    print("\n" + "="*70)
    print(" [4/5] BENCHMARKING MULTI-FRAME TEMPORAL VIDEO CLASSIFICATION")
    print("="*70)

    video_dir = os.path.expanduser("~/.config/VisionArchive/uploaded_videos")
    videos = glob.glob(os.path.join(video_dir, "*.mp4"))[:5]

    if not videos:
        print("  • No test videos found. Skipping video pipeline benchmark.")
        return {}

    vid_benchmarks = []
    for v_path in videos:
        fn = os.path.basename(v_path)
        t0 = time.perf_counter()
        frames = extract_frames(v_path)
        extract_time = (time.perf_counter() - t0) * 1000

        if not frames:
            continue

        t1 = time.perf_counter()
        v_emb = generate_video_embedding(frames)
        emb_time = (time.perf_counter() - t1) * 1000

        t2 = time.perf_counter()
        pred_label = classify_video(v_emb)
        cls_time = (time.perf_counter() - t2) * 1000

        total_time = extract_time + emb_time + cls_time
        fps = len(frames) / (total_time / 1000.0)

        vid_benchmarks.append({
            "filename": fn,
            "frames_extracted": len(frames),
            "extraction_ms": round(extract_time, 2),
            "embedding_ms": round(emb_time, 2),
            "classification_ms": round(cls_time, 2),
            "total_ms": round(total_time, 2),
            "effective_fps": round(fps, 1),
            "predicted_label": pred_label,
        })
        print(f"  • {fn[:28]}... ({len(frames)} frames) -> '{pred_label}' in {total_time:.1f}ms ({fps:.1f} FPS)")

    avg_total_ms = np.mean([b["total_ms"] for b in vid_benchmarks])
    avg_fps = np.mean([b["effective_fps"] for b in vid_benchmarks])
    print(f"  • Average Video Analysis Latency: {avg_total_ms:.1f} ms / video ({avg_fps:.1f} FPS processing speed)")

    return {
        "video_count_tested": len(vid_benchmarks),
        "avg_video_latency_ms": round(avg_total_ms, 2),
        "avg_fps": round(avg_fps, 2),
        "sample_results": vid_benchmarks,
    }

def benchmark_faiss_vector_search():
    print("\n" + "="*70)
    print(" [5/5] BENCHMARKING FAISS VECTOR SEARCH SCALING (IndexFlatIP, 512-D)")
    print("="*70)

    dim = 512
    corpus_sizes = [100, 1000, 5000, 10000, 50000]
    k_values = [1, 5, 10, 50]

    scaling_results = {}

    for N in corpus_sizes:
        np.random.seed(42)
        raw_corpus = np.random.randn(N, dim).astype("float32")
        faiss.normalize_L2(raw_corpus)

        index = faiss.IndexFlatIP(dim)
        t_build0 = time.perf_counter()
        index.add(raw_corpus)
        build_time_ms = (time.perf_counter() - t_build0) * 1000

        query_latencies = {}
        for k in k_values:
            if k > N:
                continue
            q_vecs = np.random.randn(10, dim).astype("float32")
            faiss.normalize_L2(q_vecs)

            t_q0 = time.perf_counter()
            for qv in q_vecs:
                D, I = index.search(np.array([qv]), k)
            lat_per_query_us = ((time.perf_counter() - t_q0) / len(q_vecs)) * 1_000_000  # microseconds
            query_latencies[f"k={k}"] = round(lat_per_query_us, 2)

        qps = 1_000_000.0 / query_latencies.get("k=10", 100.0)
        scaling_results[f"N={N}"] = {
            "index_build_ms": round(build_time_ms, 2),
            "query_latency_us": query_latencies,
            "queries_per_sec": round(qps, 1),
            "memory_kb": round((N * dim * 4) / 1024, 2),
        }
        print(f"  • Corpus N={N:>5}: Build={build_time_ms:6.2f}ms | Query(k=10)={query_latencies.get('k=10', 0):6.1f} μs | Throughput={qps:8.0f} QPS | Mem={scaling_results[f'N={N}']['memory_kb']:6.0f} KB")

    return scaling_results

def main():
    print("*"*70)
    print(" VISIONARCHIVE AI — EMPIRICAL MODEL BENCHMARKING ENGINE")
    print("*"*70)
    
    specs = get_system_specs()
    print("System Environment:")
    for k, v in specs.items():
        print(f"  - {k}: {v}")

    clip_metrics = benchmark_clip()
    face_metrics = benchmark_face_verification()
    cluster_metrics = benchmark_clustering()
    video_metrics = benchmark_video_pipeline()
    faiss_metrics = benchmark_faiss_vector_search()

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": specs,
        "clip_evaluation": clip_metrics,
        "face_verification_evaluation": face_metrics,
        "graph_clustering_evaluation": cluster_metrics,
        "video_pipeline_evaluation": video_metrics,
        "faiss_ann_scaling": faiss_metrics,
    }

    out_file = os.path.join(BASE_DIR, "benchmarks", "benchmark_results.json")
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*70)
    print(f" [+] All quantitative benchmarks completed successfully!")
    print(f" [+] Empirical metrics saved to: {out_file}")
    print("="*70)

if __name__ == "__main__":
    main()
