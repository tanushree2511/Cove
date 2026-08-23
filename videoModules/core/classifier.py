import numpy as np
import json
from .embedder import encode_text

LABEL_DEFINITIONS = {
    # --- Everyday Life & People ---
    "person talking": {"group": "people", "prompts": ["a person talking to the camera", "someone speaking", "a close-up of a person talking"]},
    "person smiling": {"group": "people", "prompts": ["a person smiling", "someone looking happy", "a portrait of a smiling person"]},
    "group of people": {"group": "people", "prompts": ["a group of people", "a crowd", "many people gathered together"]},
    "selfie video": {"group": "people", "prompts": ["a selfie video", "someone filming themselves", "a vlogger looking at camera"]},
    "party or celebration": {"group": "people", "prompts": ["a party", "people celebrating", "a festive gathering with friends"]},
    "children playing": {"group": "people", "prompts": ["children playing", "kids having fun", "young children running around"]},
    
    # --- Nature & Outdoors ---
    "forest or trees": {"group": "nature", "prompts": ["a dense forest", "trees in nature", "woodland scenery"]},
    "beach or ocean": {"group": "nature", "prompts": ["a sandy beach", "ocean waves crashing", "coastline scenery"]},
    "mountains": {"group": "nature", "prompts": ["high mountains", "mountain landscape", "snowy mountain peaks"]},
    "sunset or sunrise": {"group": "nature", "prompts": ["a beautiful sunset", "sun setting in the sky", "colorful sunrise"]},
    "snow or winter": {"group": "nature", "prompts": ["snow falling", "a winter landscape", "ground covered in snow"]},
    "underwater nature": {"group": "nature", "prompts": ["underwater marine life", "swimming underwater", "fishes in the ocean"]},
    "flower garden": {"group": "nature", "prompts": ["colorful flowers", "a blooming garden", "close up of a flower"]},
    
    # --- Animals & Pets ---
    "dog playing": {"group": "animals", "prompts": ["a dog playing", "a happy dog", "someone walking a dog"]},
    "cat resting": {"group": "animals", "prompts": ["a cat sleeping or resting", "a domestic cat", "a kitten"]},
    "bird flying": {"group": "animals", "prompts": ["a bird flying in the sky", "a flock of birds", "a bird perched on a branch"]},
    "wild animal": {"group": "animals", "prompts": ["a wild animal", "wildlife documentary footage", "animal in the wild"]},
    "fish or marine life": {"group": "animals", "prompts": ["fish swimming", "aquarium", "marine animals like jellyfish or fish"]},
    
    # --- Vehicles & Travel ---
    "car driving": {"group": "travel", "prompts": ["a car driving on a road", "driving view from inside a car", "traffic on a street"]},
    "airplane flying": {"group": "travel", "prompts": ["an airplane in the sky", "a plane taking off", "looking out an airplane window"]},
    "train moving": {"group": "travel", "prompts": ["a train on train tracks", "subway moving", "riding a train"]},
    "city street": {"group": "travel", "prompts": ["a busy city street", "urban architecture", "buildings and skyscrapers"]},
    
    # --- Home & Activities ---
    "cooking or food": {"group": "home", "prompts": ["cooking food in a kitchen", "a delicious meal", "someone preparing food"]},
    "eating or drinking": {"group": "home", "prompts": ["someone eating food", "drinking from a cup", "enjoying a meal"]},
    "reading a book": {"group": "home", "prompts": ["reading a book", "studying at a desk", "looking at pages of a book"]},
    "working on computer": {"group": "home", "prompts": ["typing on a laptop", "working at a computer desk", "staring at a screen"]},
    "working out": {"group": "home", "prompts": ["lifting weights", "exercising at a gym", "doing fitness training"]},
    "playing music": {"group": "home", "prompts": ["playing a musical instrument", "playing guitar or piano", "a musical performance"]},
    
    # --- Media & Formats ---
    "screen recording": {"group": "media", "prompts": ["a computer screen recording", "screencast video", "software interface"]},
    "animation or cartoon": {"group": "media", "prompts": ["a 3d animated movie", "cartoon animation", "CGI graphics"]},
    "news broadcast": {"group": "media", "prompts": ["a news anchor on television", "a news broadcast", "TV news graphics"]},
    "text on screen": {"group": "media", "prompts": ["text written on a screen", "title card", "presentation slides"]},
    "abstract visuals": {"group": "media", "prompts": ["abstract colorful visuals", "kaleidoscope patterns", "generated visual art"]},
    "historical footage": {"group": "media", "prompts": ["black and white historical footage", "old vintage video", "sepia tone classic video"]}
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
        
    norm = np.linalg.norm(video_embedding)
    if norm > 0:
        video_embedding = video_embedding / norm
    
    if video_embedding.ndim == 1:
        video_embedding = np.expand_dims(video_embedding, axis=0)
        
    # 1. Compute super-category probabilities P(group)
    super_logits = 100.0 * (video_embedding @ super_features.T)
    super_probs = softmax(super_logits)  # shape: [1, 5]
    
    # 2. Compute fine-grained category probabilities P(label)
    label_logits = 100.0 * (video_embedding @ text_features.T)
    label_probs = softmax(label_logits)  # shape: [1, 154]
    
    # 3. Apply Bayesian Gating: P(label) = P_flat(label) * P(group_of_label)
    super_keys = list(SUPER_CATEGORIES.keys())
    group_probs = []
    for label in LABELS:
        group = LABEL_DEFINITIONS[label]["group"]
        group_idx = super_keys.index(group)
        group_probs.append(super_probs[0, group_idx])
        
    group_probs = np.array(group_probs)  # shape: [154]
    
    # Joint probability
    joint_probs = label_probs[0] * group_probs
    
    # 4. Exemplar Learning Boost
    try:
        from core.database import get_all_feedback
        feedback_list = get_all_feedback()
    except Exception:
        feedback_list = []
        
    feedback_boosts = np.zeros(len(LABELS))
    for corrected_label, embedding_str in feedback_list:
        if corrected_label in LABELS and embedding_str:
            try:
                emb = np.array(json.loads(embedding_str)).astype(np.float32)
                emb_norm = np.linalg.norm(emb)
                if emb_norm > 0:
                    emb = emb / emb_norm
                
                sim = np.clip(np.dot(video_embedding[0], emb), 0.0, 1.0)
                
                if sim > 0.80:
                    boost = 2.0 * ((sim - 0.80) / 0.20)
                    label_idx = LABELS.index(corrected_label)
                    feedback_boosts[label_idx] = max(feedback_boosts[label_idx], boost)
            except Exception:
                pass
                
    joint_probs = joint_probs + feedback_boosts
    
    # Normalize joint probabilities
    joint_probs = joint_probs / np.sum(joint_probs)
    
    # 5. Multi-Label Extraction
    max_prob = np.max(joint_probs)
    selected_with_probs = []
    
    for i, prob in enumerate(joint_probs):
        if prob >= 0.40 * max_prob and prob > 0.02:
            selected_with_probs.append((LABELS[i], prob))
            
    selected_with_probs.sort(key=lambda x: x[1], reverse=True)
    selected_labels = [x[0] for x in selected_with_probs]
    
    return ", ".join(selected_labels)
