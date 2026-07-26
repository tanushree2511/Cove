import streamlit as st
import os
import json
import numpy as np
from search_engine import SearchEngine
from vector_storage import VectorStorage
from person_manager import PersonManager
from PIL import Image
from vision_config import CONFIG

# --- PAGE CONFIG ---
st.set_page_config(page_title="Vision Archive AI", layout="wide", page_icon="👁️")

# --- CSS TO HIDE STREAMLIT BRANDING & LOGS ---
st.markdown("""
    <style>
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- LOAD ENGINES ---
@st.cache_resource
def load_search_engine():
    try:
        return SearchEngine()
    except Exception:
        return None 

@st.cache_resource
def load_data():
    # Fix: Explicitly load face embeddings for the face storage
    storage = VectorStorage(index_path=CONFIG.faiss_index_path, vector_path=CONFIG.embeddings_file)  # Face embeddings
    search_storage = VectorStorage(index_path=CONFIG.search_index_path, vector_path=CONFIG.vector_path)  # CLIP semantic search
    pm = PersonManager()
    return storage, search_storage, pm

searcher = load_search_engine()
storage, search_storage, pm = load_data()

if not pm.people:
    st.warning("Person Database is empty. Load or cluster images to enable the person-specific views.")

if search_storage.vector_matrix is None:
    st.warning(f"Semantic index missing vector cache. Run 'python reindex_search.py' to populate {CONFIG.vector_path}")

# --- SIDEBAR ---
st.sidebar.title("👁️ Vision Archive")
# Added "Detective Mode" to the list
mode = st.sidebar.radio("Mode", ["Semantic Search", "Detective Mode", "Face Gallery", "System Stats"])

# ==========================================
# MODE 1: INTELLIGENT SEARCH (Global)
# ==========================================
if mode == "Semantic Search":
    st.title("🔎 Global Search")
    
    search_type = st.radio("Search Method", ["Text Description", "Reverse Image Search"], horizontal=True)
    query_vec = None
    
    if search_type == "Text Description":
        query = st.text_input("Describe a photo...", placeholder="e.g., A man smiling in a suit")
        if query and searcher:
            query_vec = searcher.get_text_embedding(query)

    elif search_type == "Reverse Image Search":
        uploaded_file = st.file_uploader("Upload an image to find similar ones", type=["jpg", "png", "jpeg"])
        if uploaded_file is not None and searcher:
            image = Image.open(uploaded_file)
            st.image(image, caption="Query Image", width=200)
            with st.spinner("Analyzing..."):
                query_vec = searcher.get_image_embedding(image)

    if query_vec is not None:
        # FAISS Search (uses CLIP search index, not face index)
        # Reshape to (1, 512) and ensure float32
        q = np.array([query_vec], dtype="float32")
        results = search_storage.search(q, k=20)
        
        st.subheader("Results")
        cols = st.columns(5)
        for i, res in enumerate(results):
            path = res['path']
            score = res['score']
            if score > 0.15: 
                with cols[i % 5]:
                    if os.path.exists(path):
                        st.image(path, caption=f"Match: {int(score*100)}%", width="stretch")

# ==========================================
# MODE 2: DETECTIVE MODE (Identity + Concept)
# ==========================================
elif mode == "Detective Mode":
    st.title("🕵️ Detective Search")
    st.markdown("Find specific concepts **within** a specific person's timeline.")

    col1, col2 = st.columns(2)
    
    with col1:
        # 1. Select Person
        person_options = []
        # Sort so named people appear first
        sorted_people = sorted(pm.people.items(), key=lambda x: (x[1]['name'] == "Unknown", len(x[1]['photos'])), reverse=True)
        
        for pid, data in sorted_people:
            if pid == "Person_-1": continue
            count = len(data['photos'])
            if count > 2: 
                person_options.append(f"{data['name']} ({pid}) - {count} photos")

        if person_options:
            selected_person = st.selectbox("1. Select Person:", options=person_options)
        else:
            st.info("No clustered people are available yet.")
            selected_person = None

    with col2:
        # 2. Enter Concept
        concept = st.text_input("2. Filter by Context:", placeholder="e.g. 'Sunglasses', 'Blue Shirt', 'Eating'")

    if selected_person and concept and searcher:
        # Parse Person ID from string "Name (Person_X) - N photos"
        person_id = selected_person.split("(")[1].split(")")[0]
        
        st.divider()
        st.write(f"Searching for **'{concept}'** inside **{person_id}'s** album...")
        
        # A. Get the Person's Photos (Identity Set)
        candidate_paths = pm.people[person_id]['photos']
        
        # B. Get the Concept Vector (Meaning Set)
        text_vec = searcher.get_text_embedding(concept)
        # all_scores = np.dot(storage.vectors, text_vec) # REMOVED (No direct vector access)
        
        # Build path map from CLIP search index (semantic vectors)
        # C. INTERSECTION
        final_results = []
        for path in candidate_paths:
            # We need the CLIP vector index for this specific file
            vec = search_storage.get_vector_by_path(path)
            if vec is None:
                continue
            score = float(np.dot(vec, text_vec))
            final_results.append((path, score))
        
        # D. Sort by Relevance
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        # E. Display
        cols = st.columns(5)
        found_count = 0
        for i, (path, score) in enumerate(final_results):
            # Show top 20, but only if they are somewhat relevant
            if i < 20 and score > 0.18:
                found_count += 1
                with cols[i % 5]:
                    if os.path.exists(path):
                        st.image(path, caption=f"{score:.2f}", width="stretch")
        
        if found_count == 0:
            st.warning(f"No photos of {person_id} matched '{concept}'.")

# ==========================================
# MODE 3: FACE GALLERY (Paginated)
# ==========================================
elif mode == "Face Gallery":
    st.title("👤 People Gallery")
    
    all_people = sorted(pm.people.items(), key=lambda x: len(x[1]['photos']), reverse=True)
    valid_people = [p for p in all_people if p[0] != "Person_-1" and len(p[1]['photos']) >= 2]
    
    ITEMS_PER_PAGE = 10
    if 'page' not in st.session_state: st.session_state.page = 0
    total_pages = max(1, len(valid_people) // ITEMS_PER_PAGE)
    
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if st.button("⬅️ Previous") and st.session_state.page > 0:
            st.session_state.page -= 1
            st.rerun()
    with c2:
        st.write(f"**Page {st.session_state.page + 1} of {total_pages}**")
    with c3:
        if st.button("Next ➡️") and st.session_state.page < total_pages - 1:
            st.session_state.page += 1
            st.rerun()

    start_idx = st.session_state.page * ITEMS_PER_PAGE
    current_batch = valid_people[start_idx : start_idx + ITEMS_PER_PAGE]

    for person_id, data in current_batch:
        with st.expander(f"{data['name']} ({len(data['photos'])} photos)", expanded=True):
            c_a, c_b = st.columns([3, 1])
            new_name = c_a.text_input("Name", value=data['name'], key=f"name_{person_id}", label_visibility="collapsed")
            if c_b.button("Save", key=f"btn_{person_id}"):
                pm.rename_person(person_id, new_name)
                st.success("Saved!")
                st.rerun()

            photos = data['photos'][:8]
            cols = st.columns(8)
            for i, p_path in enumerate(photos):
                if os.path.exists(p_path):
                    with cols[i]:
                        st.image(p_path, width="stretch")

# ==========================================
# MODE 4: STATS
# ==========================================
elif mode == "System Stats":
    st.title("📊 Database Stats")
    col1, col2 = st.columns(2)
    col1.metric("Total Photos", len(storage.paths))
    col2.metric("Unique People", len(pm.people))
    st.json(pm.people)