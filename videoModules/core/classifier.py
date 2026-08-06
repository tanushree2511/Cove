import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
import json

# Lazy loading to prevent hanging on imports
_model = None
_processor = None
model_id = "openai/clip-vit-base-patch32"
device = "cuda" if torch.cuda.is_available() else "cpu"

def get_clip_model():
    global _model, _processor
    if _model is None:
        print(f"Loading CLIP model on {device}...")
        _model = CLIPModel.from_pretrained(model_id).to(device)
        _processor = CLIPProcessor.from_pretrained(model_id)
    return _model, _processor

LABEL_DEFINITIONS = {
    # --- UCF101 Actions (Human Activities) ---
    "applying eye makeup": {"group": "human_action", "prompts": ["applying eye makeup", "a person applying eye makeup", "someone putting on eye makeup"]},
    "applying lipstick": {"group": "human_action", "prompts": ["applying lipstick", "a person applying lipstick", "someone putting on lipstick"]},
    "archery": {"group": "human_action", "prompts": ["archery", "a person doing archery", "shooting a bow and arrow"]},
    "baby crawling": {"group": "human_action", "prompts": ["baby crawling", "a cute baby crawling on the floor", "an infant crawling"]},
    "balance beam": {"group": "human_action", "prompts": ["balance beam gymnastics", "a gymnast on a balance beam", "performing on a balance beam"]},
    "band marching": {"group": "human_action", "prompts": ["band marching", "a marching band performing", "musicians marching in a parade"]},
    "baseball pitch": {"group": "human_action", "prompts": ["baseball pitch", "a baseball player pitching the ball", "a pitcher throwing a baseball"]},
    "playing basketball": {"group": "human_action", "prompts": ["playing basketball", "a basketball game", "people playing basketball"]},
    "basketball dunk": {"group": "human_action", "prompts": ["basketball dunk", "a basketball player dunking", "slam dunk in basketball"]},
    "bench press": {"group": "human_action", "prompts": ["bench press", "someone doing bench press weightlifting", "lifting weights on a bench"]},
    "biking": {"group": "human_action", "prompts": ["biking", "riding a bicycle", "a person riding a bike"]},
    "playing billiards": {"group": "human_action", "prompts": ["playing billiards", "playing pool or snooker", "someone hitting a billiard ball"]},
    "blow drying hair": {"group": "human_action", "prompts": ["blow drying hair", "a person blow drying their hair", "using a hair dryer"]},
    "blowing candles": {"group": "human_action", "prompts": ["blowing out birthday candles", "blowing candles on a cake", "someone blowing out candles"]},
    "body weight squats": {"group": "human_action", "prompts": ["doing squats", "body weight squats exercise", "someone doing squats"]},
    "bowling": {"group": "human_action", "prompts": ["bowling", "a person bowling", "throwing a bowling ball"]},
    "boxing punching bag": {"group": "human_action", "prompts": ["boxing a punching bag", "someone training with a heavy bag", "punching bag exercise"]},
    "boxing speed bag": {"group": "human_action", "prompts": ["boxing a speed bag", "hitting a speed bag", "speed bag boxing training"]},
    "breast stroke swimming": {"group": "human_action", "prompts": ["breast stroke swimming", "swimming breaststroke", "a swimmer doing breaststroke"]},
    "brushing teeth": {"group": "human_action", "prompts": ["brushing teeth", "a person brushing their teeth", "someone cleaning their teeth"]},
    "clean and jerk weightlifting": {"group": "human_action", "prompts": ["clean and jerk weightlifting", "olympic weightlifting clean and jerk", "lifting a barbell"]},
    "cliff diving": {"group": "human_action", "prompts": ["cliff diving", "a person jumping off a cliff into water", "diving off a high cliff"]},
    "cricket bowling": {"group": "human_action", "prompts": ["cricket bowling", "a bowler throwing a cricket ball", "playing cricket"]},
    "cricket shot": {"group": "human_action", "prompts": ["cricket shot", "a batsman hitting a cricket ball", "cricket batting"]},
    "cutting in kitchen": {"group": "human_action", "prompts": ["cutting in kitchen", "chopping vegetables in kitchen", "cutting food with a knife"]},
    "diving": {"group": "human_action", "prompts": ["diving", "a person diving into a swimming pool", "high springboard diving"]},
    "drumming": {"group": "human_action", "prompts": ["drumming", "playing the drums", "a drummer playing a drum kit"]},
    "fencing": {"group": "human_action", "prompts": ["fencing sport", "two people fencing with swords", "sword fighting fencing"]},
    "field hockey penalty": {"group": "human_action", "prompts": ["field hockey penalty shot", "playing field hockey", "field hockey game"]},
    "floor gymnastics": {"group": "human_action", "prompts": ["floor gymnastics", "gymnast doing floor routine", "performing gymnastics tumbling"]},
    "catching a frisbee": {"group": "human_action", "prompts": ["catching a frisbee", "playing frisbee", "throwing and catching a frisbee"]},
    "front crawl swimming": {"group": "human_action", "prompts": ["front crawl swimming", "freestyle swimming", "swimmer doing front crawl"]},
    "golf swing": {"group": "human_action", "prompts": ["golf swing", "a golfer hitting a golf ball", "playing golf"]},
    "haircut": {"group": "human_action", "prompts": ["getting a haircut", "hairdresser cutting hair", "barber cutting hair with scissors"]},
    "hammering": {"group": "human_action", "prompts": ["hammering a nail", "using a hammer", "someone hammering"]},
    "hammer throw": {"group": "human_action", "prompts": ["hammer throw track and field", "athlete throwing a hammer", "hammer throw event"]},
    "handstand pushups": {"group": "human_action", "prompts": ["handstand pushups", "doing pushups while in a handstand", "handstand pushup exercise"]},
    "handstand walking": {"group": "human_action", "prompts": ["handstand walking", "walking on hands", "someone doing a handstand walk"]},
    "head massage": {"group": "human_action", "prompts": ["getting a head massage", "scalp massage", "someone massaging a head"]},
    "high jump": {"group": "human_action", "prompts": ["high jump track and field", "athlete doing high jump", "jumping over a high bar"]},
    "horse racing": {"group": "human_action", "prompts": ["horse racing", "jockeys riding horses in a race", "jockey on a racing horse"]},
    "horse riding": {"group": "human_action", "prompts": ["horse riding", "riding a horse", "a person sitting on a horse"]},
    "hula hoop": {"group": "human_action", "prompts": ["hula hooping", "playing with a hula hoop", "someone using a hula hoop"]},
    "ice dancing": {"group": "human_action", "prompts": ["ice dancing", "figure skating couple dancing on ice", "ice skaters performing"]},
    "javelin throw": {"group": "human_action", "prompts": ["javelin throw track and field", "athlete throwing a javelin", "throwing a spear"]},
    "juggling balls": {"group": "human_action", "prompts": ["juggling balls", "a juggler juggling three or more balls", "juggling"]},
    "jumping jacks": {"group": "human_action", "prompts": ["doing jumping jacks", "jumping jacks exercise", "someone doing jumping jacks"]},
    "jumping rope": {"group": "human_action", "prompts": ["jumping rope", "skipping rope", "someone skipping rope"]},
    "kayaking": {"group": "human_action", "prompts": ["kayaking in water", "paddling a kayak", "kayaker on a river or lake"]},
    "knitting": {"group": "human_action", "prompts": ["knitting wool", "someone knitting a sweater", "hand knitting with needles"]},
    "long jump": {"group": "human_action", "prompts": ["long jump track and field", "athlete performing a long jump", "jumping into sand"]},
    "doing lunges": {"group": "human_action", "prompts": ["doing lunges exercise", "lunges workout", "someone doing lunges"]},
    "military parade": {"group": "human_action", "prompts": ["military parade", "soldiers marching in formation", "army parade"]},
    "mixing batter": {"group": "human_action", "prompts": ["mixing batter in bowl", "whisking ingredients", "baking and mixing"]},
    "mopping floor": {"group": "human_action", "prompts": ["mopping the floor", "cleaning floor with a mop", "someone mopping"]},
    "using nunchucks": {"group": "human_action", "prompts": ["using nunchucks", "swinging nunchaku", "martial arts with nunchucks"]},
    "parallel bars gymnastics": {"group": "human_action", "prompts": ["parallel bars gymnastics", "performing on parallel bars", "gymnast on parallel bars"]},
    "pizza tossing": {"group": "human_action", "prompts": ["pizza tossing", "spinning and tossing pizza dough", "pizza chef spinning dough"]},
    "playing cello": {"group": "human_action", "prompts": ["playing cello", "a cellist playing cello", "cello musical performance"]},
    "playing daf": {"group": "human_action", "prompts": ["playing daf frame drum", "daf performance", "playing a Persian frame drum"]},
    "playing dhol": {"group": "human_action", "prompts": ["playing dhol drum", "dhol performance", "playing a Punjabi dhol drum"]},
    "playing flute": {"group": "human_action", "prompts": ["playing flute", "a flutist playing the flute", "flute solo performance"]},
    "playing guitar": {"group": "human_action", "prompts": ["playing guitar", "someone playing acoustic or electric guitar", "guitarist playing"]},
    "playing piano": {"group": "human_action", "prompts": ["playing piano", "a pianist playing the piano", "grand piano performance"]},
    "playing sitar": {"group": "human_action", "prompts": ["playing sitar", "sitar performance", "playing Indian sitar"]},
    "playing tabla": {"group": "human_action", "prompts": ["playing tabla drums", "tabla performance", "playing Indian tabla"]},
    "playing violin": {"group": "human_action", "prompts": ["playing violin", "a violinist playing violin", "violin musical performance"]},
    "pole vaulting": {"group": "human_action", "prompts": ["pole vaulting", "athlete doing a pole vault", "jumping over bar with pole"]},
    "pommel horse gymnastics": {"group": "human_action", "prompts": ["pommel horse gymnastics", "performing on a pommel horse", "gymnast on pommel horse"]},
    "doing pull ups": {"group": "human_action", "prompts": ["doing pull ups", "pull up exercise on bar", "someone doing pullups"]},
    "punching": {"group": "human_action", "prompts": ["punching", "throwing a punch", "boxing punching"]},
    "doing push ups": {"group": "human_action", "prompts": ["doing push ups", "pushups exercise", "someone doing pushups"]},
    "rafting": {"group": "human_action", "prompts": ["white water rafting", "river rafting", "people in an inflatable raft"]},
    "indoor rock climbing": {"group": "human_action", "prompts": ["indoor rock climbing", "climbing a climbing wall", "rock climbing indoors"]},
    "rope climbing": {"group": "human_action", "prompts": ["rope climbing", "climbing up a rope", "rope climb exercise"]},
    "rowing a boat": {"group": "human_action", "prompts": ["rowing a boat", "rowing sport", "crew rowing crew team"]},
    "salsa spinning": {"group": "human_action", "prompts": ["salsa dancing", "salsa spinning", "couple dancing salsa"]},
    "shaving beard": {"group": "human_action", "prompts": ["shaving beard", "a man shaving his beard", "shaving face with razor"]},
    "shotput throw": {"group": "human_action", "prompts": ["shotput throw track and field", "athlete throwing shotput", "shot put event"]},
    "skateboarding": {"group": "human_action", "prompts": ["skateboarding", "riding a skateboard", "skateboard tricks"]},
    "skiing": {"group": "human_action", "prompts": ["skiing on snow", "downhill snow skiing", "a skier skiing"]},
    "riding a jetski": {"group": "human_action", "prompts": ["riding a jetski", "jet skiing on water", "riding a personal watercraft"]},
    "sky diving": {"group": "human_action", "prompts": ["sky diving", "parachuting", "skydiver falling through the air"]},
    "soccer juggling": {"group": "human_action", "prompts": ["soccer juggling", "juggling a soccer ball with feet", "keepie uppies"]},
    "soccer penalty kick": {"group": "human_action", "prompts": ["soccer penalty kick", "shooting a soccer penalty", "kicking soccer ball"]},
    "still rings gymnastics": {"group": "human_action", "prompts": ["still rings gymnastics", "performing on gymnastic rings", "gymnast on rings"]},
    "sumo wrestling": {"group": "human_action", "prompts": ["sumo wrestling match", "sumo wrestlers fighting", "sumo bout"]},
    "surfing": {"group": "human_action", "prompts": ["surfing on a wave", "surfer riding a wave", "surfing"]},
    "swinging": {"group": "human_action", "prompts": ["swinging on a swing", "someone on a playground swing", "child swinging"]},
    "table tennis shot": {"group": "human_action", "prompts": ["playing table tennis", "ping pong match", "hitting table tennis ball"]},
    "tai chi": {"group": "human_action", "prompts": ["doing tai chi", "tai chi martial arts", "performing slow tai chi movements"]},
    "tennis swing": {"group": "human_action", "prompts": ["tennis swing", "playing tennis", "hitting tennis ball with racket"]},
    "throwing discus": {"group": "human_action", "prompts": ["discus throw track and field", "athlete throwing discus", "discus throw"]},
    "trampoline jumping": {"group": "human_action", "prompts": ["jumping on a trampoline", "trampoline jumping", "someone bouncing on trampoline"]},
    "typing on keyboard": {"group": "human_action", "prompts": ["typing on keyboard", "typing on computer", "hands typing on keyboard"]},
    "uneven bars gymnastics": {"group": "human_action", "prompts": ["uneven bars gymnastics", "performing on uneven bars", "female gymnast on uneven bars"]},
    "volleyball spiking": {"group": "human_action", "prompts": ["volleyball spike", "spiking a volleyball", "volleyball match"]},
    "walking with a dog": {"group": "human_action", "prompts": ["walking with a dog", "walking a dog", "person walking a dog"]},
    "wall pushups": {"group": "human_action", "prompts": ["doing wall pushups", "wall pushups exercise", "someone doing wall pushups"]},
    "writing on board": {"group": "human_action", "prompts": ["writing on board", "writing on a blackboard or whiteboard", "teacher writing"]},
    "playing with a yoyo": {"group": "human_action", "prompts": ["playing with a yoyo", "yo-yo tricks", "someone playing with a yoyo"]},

    # --- ANIMAL CATEGORIES (CATS, DOGS, AND DEEP STATES) ---
    "cat sleeping": {"group": "animal", "prompts": ["a cat sleeping", "a sleeping cat", "a cute cat sleeping", "a kitten sleeping in bed"]},
    "cat resting": {"group": "animal", "prompts": ["a cat resting", "a resting cat", "a cat lying down quietly", "a peaceful cat resting"]},
    "cat playing": {"group": "animal", "prompts": ["a cat playing", "a playful cat", "a cat playing with a toy", "kitten playing"]},
    "cat meowing": {"group": "animal", "prompts": ["a cat meowing", "a meowing cat", "a cat vocalizing", "cat meowing at camera"]},
    "cat running": {"group": "animal", "prompts": ["a cat running", "a running cat", "a cat sprinting", "fast cat running"]},
    "cat walking": {"group": "animal", "prompts": ["a cat walking", "a walking cat", "a cat walking around the room"]},
    "cat": {"group": "animal", "prompts": ["a cat", "a domestic cat", "a cute cat", "a kitten"]},
    "dog sleeping": {"group": "animal", "prompts": ["a dog sleeping", "a sleeping dog", "a cute puppy sleeping", "dog sleeping on floor"]},
    "dog resting": {"group": "animal", "prompts": ["a dog resting", "a resting dog", "a dog lying down quietly", "dog relaxing"]},
    "dog running": {"group": "animal", "prompts": ["a dog running", "a running dog", "a dog sprinting", "fast dog running"]},
    "dog playing": {"group": "animal", "prompts": ["a dog playing", "a playful dog", "a dog playing with a ball", "puppy playing"]},
    "dog barking": {"group": "animal", "prompts": ["a dog barking", "a barking dog", "a dog barking at something"]},
    "dog walking": {"group": "animal", "prompts": ["a dog walking", "a walking dog", "a dog walking on a leash"]},
    "dog": {"group": "animal", "prompts": ["a dog", "a domestic dog", "a cute puppy", "canine"]},
    "rabbit": {"group": "animal", "prompts": ["a rabbit", "a cute bunny rabbit", "a rabbit eating"]},
    "bird flying": {"group": "animal", "prompts": ["a bird flying", "a flying bird", "a bird in flight", "birds flying in sky"]},
    "bird singing": {"group": "animal", "prompts": ["a bird singing", "a bird chirping", "a singing bird"]},
    "bird": {"group": "animal", "prompts": ["a bird", "a small bird", "a wild bird"]},
    "fish swimming": {"group": "animal", "prompts": ["fish swimming", "a fish swimming in water", "fish in an aquarium", "goldfish"]},
    "lion": {"group": "animal", "prompts": ["a lion", "a wild lion", "a lion roaring", "king of the jungle"]},
    "tiger": {"group": "animal", "prompts": ["a tiger", "a wild tiger", "a tiger walking"]},
    "bear": {"group": "animal", "prompts": ["a bear", "a wild grizzly bear", "a brown bear"]},
    "elephant": {"group": "animal", "prompts": ["an elephant", "a wild elephant", "an elephant walking"]},
    "monkey": {"group": "animal", "prompts": ["a monkey", "a monkey climbing", "a wild monkey"]},
    "horse running": {"group": "animal", "prompts": ["a horse running", "a running horse", "a galloping horse"]},
    "horse": {"group": "animal", "prompts": ["a horse", "a horse standing", "a beautiful horse"]},

    # --- HUMAN FEATURES & EMOTIONS ---
    "beautiful lady smiling": {"group": "human_feature", "prompts": ["a beautiful lady smiling", "a beautiful woman smiling", "a smiling pretty woman", "a smiling beautiful girl", "attractive smiling woman"]},
    "beautiful lady crying": {"group": "human_feature", "prompts": ["a beautiful lady crying", "a beautiful woman crying", "a crying pretty woman", "a weeping beautiful girl", "sad beautiful woman crying"]},
    "woman smiling": {"group": "human_feature", "prompts": ["a woman smiling", "a smiling woman", "a happy woman", "woman grinning"]},
    "woman crying": {"group": "human_feature", "prompts": ["a woman crying", "a crying woman", "a weeping woman", "sad woman crying"]},
    "man smiling": {"group": "human_feature", "prompts": ["a man smiling", "a smiling man", "a happy man", "man grinning"]},
    "man crying": {"group": "human_feature", "prompts": ["a man crying", "a crying man", "a weeping man", "sad man crying"]},
    "child smiling": {"group": "human_feature", "prompts": ["a child smiling", "a smiling child", "a happy kid", "a smiling baby", "happy child"]},
    "child crying": {"group": "human_feature", "prompts": ["a child crying", "a crying child", "a crying baby", "sad kid crying", "weeping toddler"]},
    "person laughing": {"group": "human_feature", "prompts": ["a person laughing", "someone laughing out loud", "a laughing person", "laughter"]},
    "person talking": {"group": "human_feature", "prompts": ["a person talking", "someone speaking", "a person talking to the camera", "talking head"]},
    "person sleeping": {"group": "human_feature", "prompts": ["a person sleeping", "someone sleeping in bed", "a sleeping person", "sleeping in bed"]},
    "person dancing": {"group": "human_feature", "prompts": ["a person dancing", "someone dancing", "dancing in a room", "happy dancer"]},
    "person sitting": {"group": "human_feature", "prompts": ["a person sitting", "someone sitting down", "sitting on a chair"]},
    "person standing": {"group": "human_feature", "prompts": ["a person standing", "someone standing up", "standing in a room"]},
    "person talking on phone": {"group": "human_feature", "prompts": ["a person talking on the phone", "someone on a phone call", "using a smartphone"]},
    "crowd of people": {"group": "human_feature", "prompts": ["a crowd of people", "a group of people", "many people gathered", "audience"]},
    "person doing sign language": {"group": "human_feature", "prompts": ["person doing sign language", "someone signing", "manual communication", "American Sign Language"]},

    # --- SCENERY & ENVIRONMENT ---
    "beautiful landscape": {"group": "scenery", "prompts": ["a beautiful landscape", "scenic nature view", "beautiful scenery", "beautiful nature landscape"]},
    "sunset": {"group": "scenery", "prompts": ["a beautiful sunset", "sunset over the horizon", "sun setting", "sunset sky"]},
    "ocean waves": {"group": "scenery", "prompts": ["ocean waves crashing", "sea waves", "beach with waves", "waves in the ocean"]},
    "city street": {"group": "scenery", "prompts": ["a city street", "busy city street", "urban street scene", "city traffic"]},
    "forest": {"group": "scenery", "prompts": ["a forest with trees", "green forest scenery", "woods", "forest landscape"]},
    "rainy day": {"group": "scenery", "prompts": ["rain falling", "a rainy day", "raining outside", "water drops falling"]},
    "snowy landscape": {"group": "scenery", "prompts": ["a snowy landscape", "snow falling", "winter scenery", "snowy mountains"]},

    # --- MEDIA & OTHER ---
    "abstract video": {"group": "media", "prompts": ["an abstract video", "abstract patterns and colors", "digital art graphics"]},
    "screen recording": {"group": "media", "prompts": ["a computer screen recording", "screencast", "software demo video", "screen capture"]},
    "news broadcast": {"group": "media", "prompts": ["a news broadcast", "news anchor speaking", "tv news report", "television studio news"]}
}

LABELS = list(LABEL_DEFINITIONS.keys())

SUPER_CATEGORIES = {
    "animal": [
        "a video of an animal, pet, dog, cat, bird, rabbit, fish, or wild animal",
        "a scene showing pets, animals, or wildlife in nature or indoors",
        "an animal, pet, or wild creature"
    ],
    "human_feature": [
        "a video of a person, people, friends, portraits, faces, or human expressions",
        "someone smiling, crying, talking, laughing, sitting, standing, or interacting",
        "a group of people, a crowd, or a close-up of a human face"
    ],
    "human_action": [
        "a video of someone performing a physical activity, sport, exercise, or gymnastic routine",
        "a person playing an instrument, dancing, cooking, or doing active chores",
        "an active physical sport, action, or hobby being performed by a person"
    ],
    "scenery": [
        "a video of scenic nature, beautiful landscape, sunset, ocean waves, forest, or city street",
        "outdoor scenery, landscape view, environment, or weather condition",
        "beautiful scenery or city environment"
    ],
    "media": [
        "a computer screen recording, software presentation, digital abstract animation, or TV news broadcast",
        "screencast, media presentation, abstract patterns, or television news show",
        "abstract video or screen capture"
    ]
}

_cached_text_features = None
_cached_super_features = None

def get_cached_super_features():
    """
    Lazy-loads and caches prompt-ensembled super-category text embeddings.
    """
    global _cached_super_features
    if _cached_super_features is None:
        model, processor = get_clip_model()
        print("Precomputing ensembled text embeddings for super-categories...")
        
        super_keys = list(SUPER_CATEGORIES.keys())
        all_texts = []
        super_ranges = []
        start_idx = 0
        
        for key in super_keys:
            prompts = SUPER_CATEGORIES[key]
            all_texts.extend(prompts)
            end_idx = start_idx + len(prompts)
            super_ranges.append((start_idx, end_idx))
            start_idx = end_idx
            
        inputs = processor(text=all_texts, return_tensors="pt", padding=True).to(device)
        
        with torch.no_grad():
            text_features = model.get_text_features(**inputs)
            if hasattr(text_features, "pooler_output"):
                text_features = text_features.pooler_output
            elif not isinstance(text_features, torch.Tensor):
                text_features = text_features[0]
                
            text_features = text_features / torch.linalg.norm(text_features, dim=-1, keepdim=True)
            
            ensemble_features = []
            for start, end in super_ranges:
                super_feat = text_features[start:end].mean(dim=0)
                super_feat = super_feat / torch.linalg.norm(super_feat, dim=-1)
                ensemble_features.append(super_feat)
                
            _cached_super_features = torch.stack(ensemble_features).to(device)
            print("Successfully cached super-category text features globally.")
            
    return _cached_super_features

def get_cached_text_features():
    """
    Lazy-loads and caches prompt-ensembled text feature embeddings.
    Compiles all ~500 prompt combinations once, passes them through the text transformer,
    averages prompt embeddings per category, and saves the final normalized tensor to RAM/VRAM.
    """
    global _cached_text_features
    if _cached_text_features is None:
        model, processor = get_clip_model()
        print(f"Precomputing ensembled text embeddings for all {len(LABELS)} labels...")
        
        # Compile all prompts across all labels
        all_texts = []
        label_ranges = []
        start_idx = 0
        
        for label in LABELS:
            prompts = LABEL_DEFINITIONS[label]["prompts"]
            all_texts.extend(prompts)
            end_idx = start_idx + len(prompts)
            label_ranges.append((start_idx, end_idx))
            start_idx = end_idx
            
        print(f"Total prompts to encode: {len(all_texts)}")
        
        # Encode all prompts at once
        inputs = processor(text=all_texts, return_tensors="pt", padding=True).to(device)
        
        with torch.no_grad():
            text_features = model.get_text_features(**inputs)
            if hasattr(text_features, "pooler_output"):
                text_features = text_features.pooler_output
            elif not isinstance(text_features, torch.Tensor):
                text_features = text_features[0]
                
            # Normalize each individual prompt feature
            text_features = text_features / torch.linalg.norm(text_features, dim=-1, keepdim=True)
            
            # Average features for each label (prompt ensembling) and re-normalize
            ensemble_features = []
            for start, end in label_ranges:
                label_feat = text_features[start:end].mean(dim=0)
                label_feat = label_feat / torch.linalg.norm(label_feat, dim=-1)
                ensemble_features.append(label_feat)
                
            _cached_text_features = torch.stack(ensemble_features).to(device)
            print("Successfully cached text features globally.")
            
    return _cached_text_features

def classify_video(video_embedding):
    """
    Classifies a video using Hierarchical Gated Bayesian Zero-Shot CLIP classification with Exemplar Learning.
    Supports multi-label tagging (returning ensembled categories that exceed a soft confidence margin)
    and few-shot adaptation by boosting user-corrected categories based on embedding similarity.
    """
    text_features = get_cached_text_features()      # shape: [154, 512]
    super_features = get_cached_super_features()    # shape: [5, 512]
    
    if isinstance(video_embedding, np.ndarray):
        video_embedding = torch.from_numpy(video_embedding).to(device).float()
        
    # Ensure video_embedding is normalized
    video_embedding = video_embedding / torch.linalg.norm(video_embedding, dim=-1, keepdim=True)
    
    # Handle dimension mismatches (ensure it is 2D: [batch, features])
    if video_embedding.ndim == 1:
        video_embedding = video_embedding.unsqueeze(0)
        
    with torch.no_grad():
        # 1. Compute super-category probabilities P(group)
        super_logits = 100.0 * video_embedding @ super_features.T
        super_probs = super_logits.softmax(dim=-1)  # shape: [1, 5]
        
        # 2. Compute fine-grained category probabilities P(label)
        label_logits = 100.0 * video_embedding @ text_features.T
        label_probs = label_logits.softmax(dim=-1)  # shape: [1, 154]
        
        # 3. Apply Bayesian Gating: P(label) = P_flat(label) * P(group_of_label)
        super_keys = list(SUPER_CATEGORIES.keys())
        group_prob_list = []
        for label in LABELS:
            group = LABEL_DEFINITIONS[label]["group"]
            group_idx = super_keys.index(group)
            group_prob_list.append(super_probs[0, group_idx])
            
        group_probs = torch.stack(group_prob_list).to(device)  # shape: [154]
        
        # Joint probability
        joint_probs = label_probs[0] * group_probs
        
        # 4. Exemplar Learning Boost (Few-shot adaptation from user corrections)
        try:
            from core.database import get_all_feedback
            feedback_list = get_all_feedback()
        except Exception:
            feedback_list = []
            
        feedback_boosts = torch.zeros(len(LABELS), device=device)
        for corrected_label, embedding_str in feedback_list:
            if corrected_label in LABELS and embedding_str:
                try:
                    emb = np.array(json.loads(embedding_str)).astype("float32")
                    emb_tensor = torch.from_numpy(emb).to(device).float()
                    emb_tensor = emb_tensor / torch.linalg.norm(emb_tensor, dim=-1, keepdim=True)
                    
                    # Cosine similarity
                    sim = torch.clamp(video_embedding @ emb_tensor, min=0.0, max=1.0).item()
                    
                    # If similarity is extremely high, boost the user-corrected label
                    if sim > 0.80:
                        # Exponentially growing boost based on similarity similarity
                        boost = 2.0 * ((sim - 0.80) / 0.20)
                        label_idx = LABELS.index(corrected_label)
                        feedback_boosts[label_idx] = max(feedback_boosts[label_idx].item(), boost)
                except Exception:
                    pass
                    
        joint_probs = joint_probs + feedback_boosts
        
        # Normalize joint probabilities
        joint_probs = joint_probs / joint_probs.sum()
        
        # 5. Multi-Label Extraction (relative margin of 40% of max + absolute 2% threshold)
        max_prob = joint_probs.max().item()
        selected_with_probs = []
        
        for i, prob in enumerate(joint_probs):
            p_val = prob.item()
            if p_val >= 0.40 * max_prob and p_val > 0.02:
                selected_with_probs.append((LABELS[i], p_val))
                
        # Sort descending by probability
        selected_with_probs.sort(key=lambda x: x[1], reverse=True)
        selected_labels = [x[0] for x in selected_with_probs]
        
    return ", ".join(selected_labels)