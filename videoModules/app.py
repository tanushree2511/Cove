import streamlit as st
import requests, os, time
from datetime import datetime, timezone

API_URL = "http://127.0.0.1:8000"
st.set_page_config(layout="wide", page_title="VisionArchive AI", page_icon="🖼️")

# --- THEME MANAGEMENT ---
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🖼️ VisionArchive</div>', unsafe_allow_html=True)
    theme_mode = st.selectbox("Appearance", ["Light Mode", "Dark Mode", "OLED Black"], index=2)
    st.divider()
    menu = st.pills("Library Navigation", ["Photos", "Search", "Bulk Import", "Identities", "Discovery", "Utilities"], default="Photos")
    if not menu: menu = "Photos"
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
    .stButton>button {{ border-radius: 20px !important; font-weight: 500 !important; padding: 0.5rem 1.5rem !important; background-color: #1a73e8 !important; color: white !important; border: none !important; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg}; border-right: 1px solid {border_color}; }}
    .sidebar-logo {{ padding: 1rem 0; font-size: 24px; font-weight: 700; color: #4285f4; display: flex; align-items: center; gap: 10px; }}
</style>
""", unsafe_allow_html=True)

# --- REAL-TIME JOB MONITORING ---
def check_jobs_realtime():
    try:
        res = requests.get(f"{API_URL}/job-status", timeout=5)
        if res.status_code == 200:
            jobs = res.json()
            is_any_job_active = False
            with st.sidebar:
                for job_type, data in jobs.items():
                    if data["status"] == "processing":
                        is_any_job_active = True
                        st.info(f"⏳ {data['message']}")
                        prog = data["current"] / data["total"] if data["total"] > 0 else 0
                        st.progress(prog)
                        if st.button(f"Cancel {job_type.replace('_', ' ').title()}", key=f"cancel_{job_type}"):
                            requests.post(f"{API_URL}/cancel-job/{job_type}", timeout=5)
                    elif data["status"] in ["completed", "cancelled", "error"]:
                        if data["status"] == "completed": st.success(f"✅ {data['message']}")
                        else: st.warning(f"⚠️ {data['message']}")
                        if st.button("Clear Status", key=f"clear_{job_type}"):
                            requests.post(f"{API_URL}/clear-jobs", timeout=5); st.rerun()
            if is_any_job_active: time.sleep(2); st.rerun()
    except: pass

check_jobs_realtime()

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
                        st.video(f"{API_URL}/stream/{os.path.basename(v['path'])}")
                        st.caption(f"**Action:** {v['label']}")
                        
                        # Audio Extraction Feature
                        if st.button("🎵 Extract Audio", key=f"audio_{i}"):
                            with st.spinner("Extracting sound..."):
                                a_res = requests.post(f"{API_URL}/extract-audio", params={"video_path": v['path']}, timeout=120)
                                if a_res.status_code == 200:
                                    data = a_res.json()
                                    if "audio_url" in data:
                                        st.audio(f"{API_URL}{data['audio_url']}")
                                        st.success("Audio ready!")
                                    else: st.error(data.get("error", "Error"))
                                else: st.error("Extraction failed.")
                        st.markdown('</div>', unsafe_allow_html=True)

    elif menu == "Search":
        st.title("🔍 Semantic Intelligence Search")
        with st.expander("Upload New Video"):
            uploaded_file = st.file_uploader("Choose video...", type=["mp4"])
            if uploaded_file and st.button("Index Video"):
                with st.spinner("Analyzing..."):
                    res = requests.post(f"{API_URL}/index-video", files={"file": uploaded_file}, timeout=300)
                    if res.status_code == 200: st.toast("Indexed Successfully!", icon="📄"); st.success(f"Indexed!")
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
                            st.video(f"{API_URL}/stream/{os.path.basename(item['path'])}")
                            st.write(f"**Action:** {item['label']} | **Score:** {item['score']:.2f}")
                            if st.button("🎵 Extract Audio", key=f"search_audio_{i}"):
                                with st.spinner("Extracting..."):
                                    a_res = requests.post(f"{API_URL}/extract-audio", params={"video_path": item['path']}, timeout=120)
                                    if a_res.status_code == 200:
                                        data = a_res.json()
                                        if "audio_url" in data: st.audio(f"{API_URL}{data['audio_url']}")
                                        else: st.error(data.get("error", "No audio"))

    elif menu == "Bulk Import":
        st.title("🚀 Smart Bulk Video Indexing")
        
        # Real-time progress display in main area
        jobs = requests.get(f"{API_URL}/job-status").json()
        bulk_job = jobs.get("bulk_index", {})
        
        if bulk_job.get("status") == "processing":
            st.info(f"⏳ {bulk_job.get('message', 'Processing...')}")
            prog = bulk_job["current"] / bulk_job["total"] if bulk_job["total"] > 0 else 0
            st.progress(prog, text=f"Progress: {bulk_job['current']}/{bulk_job['total']}")
            st.button("Stop Indexing", on_click=lambda: requests.post(f"{API_URL}/cancel-job/bulk_index"))
            st.divider()
        elif bulk_job.get("status") == "completed":
            st.success(f"✅ {bulk_job.get('message')}")
            if st.button("Clear Finished Status"):
                requests.post(f"{API_URL}/clear-jobs")
                st.rerun()
            st.divider()

        dir_path = st.text_input("Enter local directory path", key="bulk_path_input")
        if st.button("Start Bulk Indexing"):
            if dir_path:
                res = requests.post(f"{API_URL}/index-bulk", params={"directory_path": dir_path}, timeout=TIMEOUT)
                if res.status_code == 200: st.toast("Bulk indexing started", icon="🚀"); st.success("Background process started!")
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
            if not persons: st.info("No identities found yet.")
            else:
                cols = st.columns(5)
                for i, p in enumerate(persons):
                    with cols[i % 5]:
                        st.image(f"{API_URL}/faces/{p['thumbnail']}", use_container_width=True)
                        name = p['name'] if p['name'] else f"Unknown #{p['id']}"
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
                        st.video(f"{API_URL}/stream/{os.path.basename(v['path'])}")
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
                            st.image(f"{API_URL}/faces/{f['thumbnail']}", use_container_width=True)
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