import numpy as np
import json
from .embedder import encode_text

LABEL_DEFINITIONS = {
    # --- Everyday Life & People ---
    "person talking": {"group": "people", "prompts": ["a video of people talking", "two people talking", "a person talking to camera", "an interview with people speaking", "someone talking"]},
    "person smiling": {"group": "people", "prompts": ["a person smiling happily", "people smiling at the camera", "a portrait of smiling people"]},
    "group of people": {"group": "people", "prompts": ["a group of multiple people gathered together", "two or more people together", "a crowd of people"]},
    "selfie video": {"group": "people", "prompts": ["a selfie video of someone filming themselves", "a vlogger holding a phone camera"]},
    "party or celebration": {"group": "people", "prompts": ["a party", "people celebrating", "a festive gathering with friends"]},
    "children playing": {"group": "people", "prompts": ["children playing", "kids having fun", "young children running around"]},
    
    # --- Nature & Outdoors ---
    "forest or trees": {"group": "nature", "prompts": ["a dense forest with green trees", "woodland nature and trees"]},
    "beach or ocean": {"group": "nature", "prompts": ["a sandy beach", "ocean waves crashing", "coastline scenery"]},
    "mountains": {"group": "nature", "prompts": ["snowy mountain peaks", "high mountains landscape"]},
    "sunset or sunrise": {"group": "nature", "prompts": ["a beautiful sunset", "sun setting in the sky", "colorful sunrise"]},
    "snow or winter": {"group": "nature", "prompts": ["snow falling", "a winter landscape", "ground covered in snow"]},
    "underwater nature": {"group": "nature", "prompts": ["underwater marine life", "swimming underwater", "fishes in the ocean"]},
    "flower garden": {"group": "nature", "prompts": ["blooming colorful flower garden", "flowers in nature"]},
    "rain or storm": {"group": "nature", "prompts": ["rain drops falling", "rainfall and storm", "rain on a window glass", "rainy weather"]},
    
    # --- Animals & Pets ---
    "dog playing": {"group": "animals", "prompts": ["a dog playing or running", "a domestic dog or puppy"]},
    "cat resting": {"group": "animals", "prompts": ["a cat resting or sleeping", "a domestic cat or kitten"]},
    "bird flying": {"group": "animals", "prompts": ["a bird flying in the sky", "a flock of birds", "a bird perched on a branch"]},
    "wild animal": {"group": "animals", "prompts": ["wild animal in nature", "wildlife documentary animals"]},
    "fish or marine life": {"group": "animals", "prompts": ["fish swimming", "aquarium", "marine animals like jellyfish or fish"]},
    
    # --- Vehicles & Travel ---
    "car driving": {"group": "travel", "prompts": ["a car driving on a road or highway", "automobile in traffic"]},
    "airplane flying": {"group": "travel", "prompts": ["an airplane in the sky", "a plane taking off", "looking out an airplane window"]},
    "train moving": {"group": "travel", "prompts": ["a train on train tracks", "subway moving", "riding a train"]},
    "city street": {"group": "travel", "prompts": ["a busy city street", "urban architecture", "buildings and skyscrapers"]},
    
    # --- Home & Activities ---
    "cooking or food": {"group": "home", "prompts": ["cooking food in a kitchen", "preparing a meal", "cooking delicious food"]},
    "eating or drinking": {"group": "home", "prompts": ["someone eating food", "drinking from a cup", "enjoying a meal"]},
    "reading a book": {"group": "home", "prompts": ["reading a book", "studying at a desk", "looking at pages of a book"]},
    "working on computer": {"group": "home", "prompts": ["typing on a laptop", "working at a computer desk", "staring at a screen"]},
    "working out": {"group": "home", "prompts": ["lifting weights", "exercising at a gym", "doing fitness training"]},
    "playing music": {"group": "home", "prompts": ["playing a musical instrument", "playing guitar or piano", "a musical performance"]},
    
    # --- Media & Formats ---
    "screen recording": {"group": "media", "prompts": ["a screen recording of a computer desktop showing software windows and mouse cursor", "a screencast capturing computer monitor operating system desktop", "screen recording of computer software and browser windows"]},
    "animation or cartoon": {"group": "media", "prompts": ["an animated cartoon movie", "animated illustrated characters", "a 3D CGI cartoon animation with animated characters"]},
    "news broadcast": {"group": "media", "prompts": ["a news anchor in a television news studio", "TV news broadcast studio with news anchor"]},
    "text on screen": {"group": "media", "prompts": ["a video of text slides with title card and text on screen", "written text presentation"]}
}


LABELS = list(LABEL_DEFINITIONS.keys())

SUPER_CATEGORIES = {
    "people": [
        "a video of a person, people, friends, or human faces",
        "someone talking, smiling, or interacting",
        "a group of people, a crowd, or a gathering"
    ],
    "nature": [
        "a video of nature, outdoors, landscapes, or scenery",
        "forests, oceans, mountains, or weather",
        "beautiful natural environments and outdoor scenes"
    ],
    "animals": [
        "a video of an animal, pet, dog, cat, or wildlife",
        "animals playing, resting, or in their habitat",
        "a creature, pet, or wild animal"
    ],
    "travel": [
        "a video of travel, vehicles, cars, trains, or planes",
        "driving, transportation, or city streets",
        "moving through a city or riding a vehicle"
    ],
    "home": [
        "a video of indoor activities, home life, or working out",
        "cooking, eating, reading, or working on a computer",
        "everyday home and indoor lifestyle activities"
    ],
    "media": [
        "a video of media, screen recordings, animations, or cartoons",
        "news broadcasts, abstract visuals, or text on screen",
        "digital graphics, historical footage, or generated video"
    ]
}


_cached_text_features = None
_cached_super_features = None

def get_cached_super_features():
    global _cached_super_features
    if _cached_super_features is None:
        print("Precomputing ensembled text embeddings for super-categories...")
        
        super_keys = list(SUPER_CATEGORIES.keys())
        ensemble_features = []
        
        for key in super_keys:
            prompts = SUPER_CATEGORIES[key]
            features = []
            for prompt in prompts:
                emb = encode_text(prompt)
                features.append(emb)
            
            super_feat = np.mean(features, axis=0)
            norm = np.linalg.norm(super_feat)
            if norm > 0:
                super_feat = super_feat / norm
            ensemble_features.append(super_feat)
            
        _cached_super_features = np.stack(ensemble_features)
        print("Successfully cached super-category text features globally.")
            
    return _cached_super_features

def get_cached_text_features():
    global _cached_text_features
    if _cached_text_features is None:
        print(f"Precomputing ensembled text embeddings for all {len(LABELS)} labels...")
        
        ensemble_features = []
        
        for label in LABELS:
            prompts = LABEL_DEFINITIONS[label]["prompts"]
            features = []
            for prompt in prompts:
                emb = encode_text(prompt)
                features.append(emb)
                
            label_feat = np.mean(features, axis=0)
            norm = np.linalg.norm(label_feat)
            if norm > 0:
                label_feat = label_feat / norm
            ensemble_features.append(label_feat)
            
        _cached_text_features = np.stack(ensemble_features)
        print("Successfully cached text features globally.")
            
    return _cached_text_features

def softmax(x):
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)

def classify_video(video_embedding):
    text_features = get_cached_text_features()      # shape: [154, 512]
    super_features = get_cached_super_features()    # shape: [5, 512]
    
    if not isinstance(video_embedding, np.ndarray):
        video_embedding = np.array(video_embedding, dtype=np.float32)
        
    video_embedding = video_embedding.reshape(-1)
    norm = np.linalg.norm(video_embedding)
    if norm > 0:
        video_embedding = video_embedding / norm
    video_embedding = np.expand_dims(video_embedding, axis=0)
        
    # Compute direct cosine similarities across all calibrated label representations
    sims = (video_embedding[0] @ text_features.T).astype(np.float32)
    
    # Exemplar Learning Boost
    try:
        from core.database import get_all_feedback
        feedback_list = get_all_feedback()
    except Exception:
        feedback_list = []
        
    for corrected_label, embedding_str in feedback_list:
        if corrected_label in LABELS and embedding_str:
            try:
                emb = np.array(json.loads(embedding_str)).astype(np.float32)
                emb_norm = np.linalg.norm(emb)
                if emb_norm > 0:
                    emb = emb / emb_norm
                
                sim = np.clip(np.dot(video_embedding[0], emb), 0.0, 1.0)
                if sim > 0.80:
                    boost = 0.05 * ((sim - 0.80) / 0.20)
                    label_idx = LABELS.index(corrected_label)
                    sims[label_idx] += boost
            except Exception:
                pass
                
    max_sim = float(np.max(sims))
    if max_sim < 0.220:
        return "video"
        
    # Adaptive relative margin filtering: select top-performing labels within 0.005 of the best match
    cutoff = max(max_sim - 0.005, 0.245)
    selected = [(LABELS[i], sims[i]) for i in range(len(LABELS)) if sims[i] >= cutoff]
    selected.sort(key=lambda x: x[1], reverse=True)
    selected_labels = [s[0] for s in selected[:3]]
    return ", ".join(selected_labels)
