import streamlit as st
import requests, os, time
from datetime import datetime, timezone

API_URL = os.getenv("VIDEO_API_URL", "http://127.0.0.1:8000")
st.set_page_config(layout="wide", page_title="VisionArchive AI", page_icon="🖼️")

# API_URL above is for server-side Python calls (requests.get/post/delete) and,
# in Docker, resolves via the internal service hostname (e.g. http://video-api:8001)
# — that hostname is NOT reachable from the user's browser. Media embedded directly
# into the page (st.video/st.audio/st.image src) is fetched BY THE BROWSER, so it
# needs a browser-reachable URL instead. Derive that from the Host header the
# browser actually used to reach this page, falling back to an explicit override.
def _get_public_api_url():
    override = os.getenv("VIDEO_API_PUBLIC_URL")
    if override:
        return override
    try:
        host_header = st.context.headers.get("Host", "")
        hostname = host_header.split(":")[0] if host_header else "localhost"
    except Exception:
        hostname = "localhost"
    return f"http://{hostname}:8001"

PUBLIC_API_URL = _get_public_api_url()

# --- THEME MANAGEMENT ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🖼️ VisionArchive</div>', unsafe_allow_html=True)
    theme_mode = st.selectbox("Appearance", ["Light Mode", "Dark Mode", "OLED Black"], index=2)
    st.divider()
    menu = st.pills("Library Navigation", ["Photos", "Search", "Bulk Import", "Identities", "Discovery", "Utilities"], default="Photos")
    if not menu: menu = "Photos"
    # Clicking a person's photo does a real browser navigation to ?view_person=<id>,
    # which starts a brand-new Streamlit session — the pills widget above resets to
    # its default ("Photos"), so force it back to Identities to actually show them.
    if "view_person" in st.query_params:
        menu = "Identities"
    st.divider()
    conf_level = st.slider("Match Accuracy", 0.0, 1.0, 0.15, 0.05)

# --- THEME COLORS ---
if theme_mode == "Dark Mode":
    bg_color = "#202124"; text_color = "#e8eaed"; card_bg = "#292a2d"; sidebar_bg = "#202124"; border_color = "#3c4043"; sub_text = "#9aa0a6"
elif theme_mode == "OLED Black":
    bg_color = "#000000"; text_color = "#ffffff"; card_bg = "#111111"; sidebar_bg = "#000000"; border_color = "#333333"; sub_text = "#888888"
else: # Light Mode
    bg_color = "#ffffff"; text_color = "#3c4043"; card_bg = "#ffffff"; sidebar_bg = "#ffffff"; border_color = "#e0e0e0"; sub_text = "#5f6368"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap');
    .stApp {{ background-color: {bg_color}; color: {text_color}; font-family: 'Google Sans', sans-serif; }}
    h1, h2, h3, .stMetric, label {{ color: {text_color} !important; font-family: 'Google Sans', sans-serif !important; }}
    .stMarkdown, p, span {{ color: {text_color}; }}
    .stCaption {{ color: {sub_text} !important; }}
    div[data-baseweb="input"] {{ border-radius: 8px !important; background-color: {card_bg} !important; border: 1px solid {border_color} !important; }}
    input {{ color: {text_color} !important; background-color: transparent !important; }}
    .video-card {{ border-radius: 12px; overflow: hidden; transition: transform 0.2s, box-shadow 0.2s; margin-bottom: 20px; background: {card_bg}; border: 1px solid {border_color}; padding: 10px; }}
    .video-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
    .stButton>button {{ 
        border-radius: 8px !important; 
        font-weight: 500 !important; 
        padding: 5px 10px !important; 
        font-size: 11px !important;
        background-color: rgba(128, 128, 128, 0.05) !important; 
        color: inherit !important; 
        border: 1px solid rgba(128, 128, 128, 0.2) !important; 
        transition: all 0.25s ease;
        width: 100% !important;
        height: auto !important;
        min-height: unset !important;
        line-height: 1.2 !important;
    }}
    .stButton>button:hover {{
        background-color: rgba(128, 128, 128, 0.15) !important;
        border-color: #1a73e8 !important;
        color: #ffffff !important;
        box-shadow: 0 0 8px rgba(26, 115, 232, 0.3) !important;
    }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg}; border-right: 1px solid {border_color}; }}
    .sidebar-logo {{ padding: 1rem 0; font-size: 24px; font-weight: 700; color: #4285f4; display: flex; align-items: center; gap: 10px; }}
</style>
""", unsafe_allow_html=True)

# --- REAL-TIME JOB MONITORING & SIDEBAR STATS (NON-BLOCKING FRAGMENT) ---
@st.fragment(run_every="3s")
def render_sidebar_stats_and_jobs():
    try:
        res_jobs = requests.get(f"{API_URL}/job-status", timeout=3)
        res_stats = requests.get(f"{API_URL}/face-stats", timeout=3)
        res_vids = requests.get(f"{API_URL}/videos", timeout=3)
        
        total_vids = len(res_vids.json().get("videos", [])) if res_vids.status_code == 200 else 0
        total_people = res_stats.json().get("total_people", 0) if res_stats.status_code == 200 else 0
        total_faces = res_stats.json().get("total_faces", 0) if res_stats.status_code == 200 else 0

        with st.sidebar:
            st.divider()
            st.markdown(f"""
            <div style="background-color: {card_bg}; border: 1px solid {border_color}; border-radius: 10px; padding: 12px; margin-bottom: 10px;">
                <div style="font-weight: 600; font-size: 13px; margin-bottom: 8px; color: #4285f4; display: flex; align-items: center; gap: 6px;">
                    📊 <span>Library Summary</span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                    <span>📹 Indexed Videos:</span> <strong>{total_vids}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                    <span>👤 Identities:</span> <strong>{total_people}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 12px;">
                    <span>🖼️ Clear Faces:</span> <strong>{total_faces}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if res_jobs.status_code == 200:
                jobs = res_jobs.json()
                for job_type, data in jobs.items():
                    if data["status"] == "processing":
                        current = data.get("current", 0)
                        total = data.get("total", 0)
                        pct = int((current / total * 100)) if total > 0 else 0
                        st.info(f"⏳ {data.get('message', 'Processing...')}")
                        st.progress(current / total if total > 0 else 0, text=f"Indexed: {current}/{total} ({pct}%)")
                        if st.button(f"Stop {job_type.replace('_', ' ').title()}", key=f"cancel_side_{job_type}"):
                            requests.post(f"{API_URL}/cancel-job/{job_type}", timeout=5)
                            st.rerun()
                    elif data["status"] in ["completed", "cancelled", "error"]:
                        if data["status"] == "completed": st.success(f"✅ {data['message']}")
                        else: st.warning(f"⚠️ {data['message']}")
                        if st.button("Clear Status", key=f"clear_side_{job_type}"):
                            requests.post(f"{API_URL}/clear-jobs", timeout=5)
                            st.rerun()
    except Exception:
        pass

render_sidebar_stats_and_jobs()

# --- MAIN CONTENT ---
try:
    TIMEOUT = 30
    if menu == "Photos":
        st.title("📂 Your Media Library")
        res = requests.get(f"{API_URL}/videos", timeout=TIMEOUT)
        if res.status_code == 200:
            videos = res.json()["videos"]
            if not videos: st.info("Your library is empty. Go to 'Bulk Import' to index videos.")
            else:
                cols = st.columns(3) # Slightly larger cards
                for i, v in enumerate(videos):
                    with cols[i % 3]:
                        st.markdown('<div class="video-card">', unsafe_allow_html=True)
                        st.video(f"{PUBLIC_API_URL}/stream/{os.path.basename(v['path'])}")
                        
                        # Split and render ensembled/multi-label tags
                        labels = [lbl.strip() for lbl in v['label'].split(",")]
                        tags_html = "".join([f'<span style="background: linear-gradient(135deg, #1a73e8, #8ab4f8); color:white; padding:4px 10px; border-radius:14px; font-size:11px; margin-right:6px; display:inline-block; margin-bottom:6px; font-weight:500; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{lbl}</span>' for lbl in labels])
                        st.markdown(f'<div style="margin-bottom: 12px; line-height: 1.6;"><strong style="color: {text_color}; margin-right: 6px;">Tags:</strong>{tags_html}</div>', unsafe_allow_html=True)
                        
                        vid_id = v.get('id')
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            # Audio Extraction Feature
                            audio_btn_key = f"audio_{vid_id}" if vid_id is not None else f"audio_fallback_{i}"
                            if st.button("🎵 Extract Audio", key=audio_btn_key):
                                with st.spinner("Extracting sound..."):
                                    a_res = requests.post(f"{API_URL}/extract-audio", params={"video_path": v['path']}, timeout=120)
                                    if a_res.status_code == 200:
                                        data = a_res.json()
                                        if "audio_url" in data:
                                            st.audio(f"{PUBLIC_API_URL}{data['audio_url']}")
                                            st.success("Audio ready!")
                                        else: st.error(data.get("error", "Error"))
                                    else: st.error("Extraction failed.")
                        with col_btn2:
                            if vid_id is not None:
                                if st.button("⚠️ Incorrect Label", key=f"incorrect_{vid_id}"):
                                    st.session_state[f"edit_label_{vid_id}"] = not st.session_state.get(f"edit_label_{vid_id}", False)
                            else:
                                st.button("⚠️ Incorrect Label", key=f"incorrect_disabled_{i}", disabled=True, help="API server must be restarted (started with --reload or manual relaunch) to enable user correction feedback.")
                                
                        if vid_id is not None and st.session_state.get(f"edit_label_{vid_id}", False):
                            st.write("---")
                            correct_val = st.text_input("Enter correct label:", value=v['label'], key=f"correct_input_{vid_id}")
                            if st.button("💾 Save", key=f"submit_correct_{vid_id}"):
                                with st.spinner("Saving correction..."):
                                    c_res = requests.post(f"{API_URL}/videos/{vid_id}/correct-label", params={"corrected_label": correct_val})
                                    if c_res.status_code == 200:
                                        st.toast("Label corrected! Re-indexing...", icon="💾")
                                        requests.post(f"{API_URL}/rebuild-index")
                                        st.success("Model learned from feedback!")
                                        st.session_state[f"edit_label_{vid_id}"] = False
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Failed to correct label.")
                        st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "Search":
        st.title("🔍 Semantic Intelligence Search")
        with st.expander("Upload New Video"):
            uploaded_file = st.file_uploader("Choose video...", type=["mp4"])
            if uploaded_file and st.button("Index Video"):
                with st.spinner("Analyzing..."):
                    res = requests.post(f"{API_URL}/index-video", files={"file": uploaded_file}, timeout=300)
                    if res.status_code == 200:
                        label_assigned = res.json().get("label", "unknown")
                        st.toast(f"Indexed: {label_assigned}", icon="📄")
                        st.success(f"Indexed Successfully! Assigned Labels: **{label_assigned}**")
        st.divider()
        col_q, col_s = st.columns([3, 1])
        with col_q:
            query = st.text_input("What activity are you looking for?", placeholder="e.g. dog walking, sign language, person biking")
        with col_s:
            conf_level = st.slider("Strictness", 0.0, 0.5, 0.23, step=0.01, help="Higher = more accurate results, Lower = more broad results")
            
        if st.button("🔍 Search Library", use_container_width=True):
            res = requests.post(f"{API_URL}/search", params={"query": query, "threshold": conf_level}, timeout=TIMEOUT)
            if res.status_code == 200:
                results = res.json()["results"]
                if not results: st.warning("No matches found.")
                else:
                    st.toast(f"Found {len(results)} results", icon="🔍")
                    cols = st.columns(2)
                    for i, item in enumerate(results):
                        with cols[i % 2]:
                            st.markdown('<div class="video-card">', unsafe_allow_html=True)
                            st.video(f"{PUBLIC_API_URL}/stream/{os.path.basename(item['path'])}")
                            
                            # Split and render ensembled/multi-label tags
                            labels = [lbl.strip() for lbl in item['label'].split(",")]
                            tags_html = "".join([f'<span style="background: linear-gradient(135deg, #1a73e8, #8ab4f8); color:white; padding:4px 10px; border-radius:14px; font-size:11px; margin-right:6px; display:inline-block; margin-bottom:6px; font-weight:500; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{lbl}</span>' for lbl in labels])
                            st.markdown(f'<div style="margin-bottom: 12px; line-height: 1.6;"><strong style="color: {text_color}; margin-right: 6px;">Tags:</strong>{tags_html}</div>', unsafe_allow_html=True)
                            st.caption(f"Match Score: {item['score']:.2f}")
                            
                            vid_id = item.get('id')
                            
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                audio_btn_key = f"search_audio_{vid_id}" if vid_id is not None else f"search_audio_fallback_{i}"
                                if st.button("🎵 Extract Audio", key=audio_btn_key):
                                    with st.spinner("Extracting sound..."):
                                        a_res = requests.post(f"{API_URL}/extract-audio", params={"video_path": item['path']}, timeout=120)
                                        if a_res.status_code == 200:
                                            data = a_res.json()
                                            if "audio_url" in data: st.audio(f"{PUBLIC_API_URL}{data['audio_url']}")
                                            else: st.error(data.get("error", "No audio"))
                            with col_btn2:
                                if vid_id is not None:
                                    if st.button("⚠️ Incorrect Label", key=f"search_incorrect_{vid_id}"):
                                        st.session_state[f"search_edit_label_{vid_id}"] = not st.session_state.get(f"search_edit_label_{vid_id}", False)
                                else:
                                    st.button("⚠️ Incorrect Label", key=f"search_incorrect_disabled_{i}", disabled=True, help="API server must be restarted (started with --reload or manual relaunch) to enable user correction feedback.")
                                    
                            if vid_id is not None and st.session_state.get(f"search_edit_label_{vid_id}", False):
                                st.write("---")
                                correct_val = st.text_input("Enter correct label:", value=item['label'], key=f"search_correct_input_{vid_id}")
                                if st.button("💾 Save Correction", key=f"search_submit_correct_{vid_id}"):
                                    with st.spinner("Saving correction..."):
                                        c_res = requests.post(f"{API_URL}/videos/{vid_id}/correct-label", params={"corrected_label": correct_val})
                                        if c_res.status_code == 200:
                                            st.toast("Label corrected! Re-indexing...", icon="💾")
                                            requests.post(f"{API_URL}/rebuild-index")
                                            st.success("Model learned from feedback!")
                                            st.session_state[f"search_edit_label_{vid_id}"] = False
                                            time.sleep(1)
                                            st.rerun()
                                        else: st.error("Failed to correct label.")
                            st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "Bulk Import":
        st.title("🚀 Smart Bulk Video Indexing")
        
        @st.fragment(run_every="3s")
        def render_bulk_import_progress():
            try:
                jobs = requests.get(f"{API_URL}/job-status", timeout=3).json()
                bulk_job = jobs.get("bulk_index", {})
                
                if bulk_job.get("status") == "processing":
                    st.info(f"⏳ {bulk_job.get('message', 'Processing...')}")
                    prog = bulk_job["current"] / bulk_job["total"] if bulk_job["total"] > 0 else 0
                    st.progress(prog, text=f"Progress: {bulk_job['current']}/{bulk_job['total']}")
                    if st.button("Stop Indexing", key="stop_bulk_main"):
                        requests.post(f"{API_URL}/cancel-job/bulk_index")
                        st.rerun()
                    st.divider()
                elif bulk_job.get("status") == "completed":
                    st.success(f"✅ {bulk_job.get('message')}")
                    if st.button("Clear Finished Status", key="clear_bulk_main"):
                        requests.post(f"{API_URL}/clear-jobs")
                        st.rerun()
                    st.divider()
            except Exception:
                pass

        render_bulk_import_progress()

        st.info(
            "📁 This runs inside a Docker container, so it can't browse your computer's file "
            "system with a raw Windows path like `C:\\Videos`. Your whole user folder "
            "(`C:\\Users\\Tanushree Chaudhary`) is mounted read-only at "
            "**`/app/videoModules/host_home`** — swap the `C:\\Users\\Tanushree Chaudhary\\` "
            "prefix on any path for that instead. For example:\n\n"
            "- `C:\\Users\\Tanushree Chaudhary\\Videos\\Captures` → "
            "`/app/videoModules/host_home/Videos/Captures`\n"
            "- `C:\\Users\\Tanushree Chaudhary\\Desktop\\clips` → "
            "`/app/videoModules/host_home/Desktop/clips`\n\n"
            "Or drop files into the **`videoModules/bulk_import/`** folder (next to this "
            "project's `docker-compose.yml`) and use the pre-filled default below instead."
        )
        dir_path = st.text_input(
            "Directory or video file path (inside the container)",
            value="/app/videoModules/bulk_import",
            key="bulk_path_input",
            help="This is a container path, not a Windows path. Anything under your user folder "
                 "is reachable via /app/videoModules/host_home/<subpath> — see the note above.",
        )
        if st.button("Start Bulk Indexing"):
            if dir_path:
                res = requests.post(f"{API_URL}/index-bulk", params={"directory_path": dir_path}, timeout=TIMEOUT)
                if res.status_code == 200: 
                    st.toast("Bulk indexing started in background!", icon="🚀")
                    st.success("Background process started! You can navigate away and use all features freely.")
                    st.rerun()
            else: st.warning("Please enter a path.")

    elif menu == "Identities":
        st.title("👤 Person & Identity Directory")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("👓 Remove Blurry Faces", help="Deletes low quality / blurry face detections from the database"):
                with st.spinner("Scanning for blurry faces..."):
                    res = requests.delete(f"{API_URL}/remove-blurred-faces", timeout=300)
                    if res.status_code == 200: 
                        st.toast(f"Removed {res.json().get('removed', 0)} blurry faces!", icon="👓")
                        time.sleep(1)
                        st.rerun()
                        
        res = requests.get(f"{API_URL}/all-persons", timeout=TIMEOUT)
        if res.status_code == 200:
            persons = res.json()["persons"]

            # Clicking a person's photo navigates here via ?view_person=<id>
            clicked_id = st.query_params.get("view_person")
            if clicked_id is not None:
                match = next((pp for pp in persons if str(pp["id"]) == clicked_id), None)
                if match:
                    st.session_state['active_p'] = match
                st.query_params.clear()

            if not persons: st.info("No identities found yet.")
            else:
                cols = st.columns(5)
                for i, p in enumerate(persons):
                    with cols[i % 5]:
                        name = p['name'] if p['name'] else f"Unknown #{p['id']}"
                        st.markdown(
                            f'<a href="?view_person={p["id"]}" target="_self" title="View videos featuring {name}">'
                            f'<img src="{PUBLIC_API_URL}/faces/{p["thumbnail"]}" '
                            f'style="width:100%; border-radius:8px; cursor:pointer; display:block;" />'
                            f'</a>',
                            unsafe_allow_html=True,
                        )
                        if st.button(name, key=f"person_btn_{p['id']}"): st.session_state['active_p'] = p
        if 'active_p' in st.session_state:
            p = st.session_state['active_p']; st.divider(); col_id, col_vids = st.columns([1, 2])
            with col_id:
                st.subheader("Edit Identity")
                new_name = st.text_input("Name this person", value=p['name'] if p['name'] else "")
                if st.button("Save Name"):
                    requests.post(f"{API_URL}/name-person/{p['id']}", params={"name": new_name}, timeout=TIMEOUT)
                    st.toast("Identity updated!", icon="👤"); st.rerun()
            with col_vids:
                st.subheader(f"Videos featuring this person")
                v_res = requests.get(f"{API_URL}/person-videos/{p['id']}", timeout=TIMEOUT)
                if v_res.status_code == 200:
                    for v in v_res.json()["videos"]:
                        st.video(f"{PUBLIC_API_URL}/stream/{os.path.basename(v['path'])}")
                        st.caption(f"Activity: {v['label']}")

    elif menu == "Discovery":
        st.title("🧩 Face Discovery & Grouping")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Run Global AI Re-clustering", use_container_width=True):
                requests.post(f"{API_URL}/cluster-faces", timeout=TIMEOUT); st.toast("Clustering started", icon="🧩"); time.sleep(1); st.rerun()
        with col2:
            if st.button("🧹 Remove Duplicate Detections", use_container_width=True):
                with st.spinner("Cleaning up..."):
                    res = requests.delete(f"{API_URL}/remove-duplicates", timeout=300)
                    if res.status_code == 200: st.toast("Duplicates removed", icon="🧹"); st.rerun()
        st.divider()
        g_res = requests.get(f"{API_URL}/face-gallery", timeout=TIMEOUT); p_res = requests.get(f"{API_URL}/all-persons", timeout=TIMEOUT)
        if g_res.status_code == 200 and p_res.status_code == 200:
            gallery = g_res.json()["gallery"]; persons_list = {str(p['id']): p for p in p_res.json()["persons"]}
            for p_id, faces in gallery.items():
                p_info = persons_list.get(p_id, {"name": "Unknown", "thumbnail": ""})
                name = p_info['name'] if p_info['name'] else f"Person #{p_id}"
                with st.expander(f"👤 {name} ({len(faces)} detections)", expanded=False):
                    cols = st.columns(6)
                    for i, f in enumerate(faces):
                        with cols[i % 6]:
                            st.image(f"{PUBLIC_API_URL}/faces/{f['thumbnail']}", use_container_width=True)
                            st.caption(f"Conf: {f['confidence']:.2f}")

    elif menu == "Utilities":
        st.title("📊 Identity Intelligence Dashboard")
        s_res = requests.get(f"{API_URL}/face-stats", timeout=TIMEOUT)
        if s_res.status_code == 200:
            stats = s_res.json()
            m1, m2, m3 = st.columns(3)
            m1.metric("Identities", stats["total_people"]); m2.metric("Detections", stats["total_faces"])
            m3.metric("Avg Face/Person", f"{stats['total_faces']/stats['total_people']:.1f}" if stats["total_people"] > 0 else "0")
            st.divider(); c1, c2 = st.columns(2)
            with c1:
                st.subheader("Face Distribution"); dist_data = stats["distribution"]
                if dist_data: st.bar_chart(dist_data)
                else: st.write("No data.")
            with c2:
                st.subheader("Detection Confidence")
                if stats["confidences"]: st.line_chart(stats["confidences"])
                else: st.write("No data.")
            st.subheader("Video Coverage")
            if stats["video_distribution"]: st.bar_chart(stats["video_distribution"])
            st.divider(); st.subheader("System Health & Cleanup")
            c_r1, c_r2 = st.columns(2)
            with c_r1:
                if st.button("🔧 Repair Search Index", use_container_width=True):
                    with st.spinner("Repairing..."):
                        res = requests.post(f"{API_URL}/rebuild-index", timeout=300)
                        if res.status_code == 200: st.toast("Search index repaired", icon="🔧"); st.success("Synced!")
            with c_r2:
                st.write("**Bulk Cleanup**")
                hours = st.number_input("Delete videos from last X hours", min_value=0.1, value=1.0, step=1.0)
                v_res = requests.get(f"{API_URL}/videos", timeout=TIMEOUT)
                if v_res.status_code == 200:
                    all_vids = v_res.json()["videos"]; to_del_count = 0; now_utc = datetime.now(timezone.utc).timestamp()
                    for vid in all_vids:
                        if vid.get("created_at"):
                            try:
                                v_time = datetime.strptime(vid["created_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
                                if now_utc - v_time < (hours * 3600): to_del_count += 1
                            except: pass
                    if to_del_count > 0:
                        st.warning(f"This will permanently delete **{to_del_count} videos** from the last {hours} hours.")
                        if st.button(f"🗑️ Confirm Deletion ({to_del_count} videos)", type="primary", use_container_width=True):
                            res = requests.delete(f"{API_URL}/videos/delete-by-time", params={"hours": hours}, timeout=300)
                            if res.status_code == 200: st.toast("Recent videos deleted", icon="🗑️"); st.rerun()
                    else: st.info(f"No videos found in the last {hours} hours.")
                    
                st.markdown("---")
                st.write("**Danger Zone**")
                if st.button("🚨 Delete ALL Videos in Database", type="primary", use_container_width=True):
                    res = requests.delete(f"{API_URL}/videos/delete-all", timeout=300)
                    if res.status_code == 200:
                        st.toast("Entire database wiped", icon="🚨")
                        st.rerun()

except Exception as e:
    st.error(f"Critical UI Error: {e}")