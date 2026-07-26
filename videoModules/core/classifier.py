import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np

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

LABELS = [
    # UCF101 Action Categories (Natural Language Formatted)
    "applying eye makeup", "applying lipstick", "archery", "baby crawling", 
    "balance beam", "band marching", "baseball pitch", "playing basketball", 
    "basketball dunk", "bench press", "biking", "playing billiards", 
    "blow drying hair", "blowing candles", "body weight squats", "bowling", 
    "boxing punching bag", "boxing speed bag", "breast stroke swimming", 
    "brushing teeth", "clean and jerk weightlifting", "cliff diving", 
    "cricket bowling", "cricket shot", "cutting in kitchen", "diving", 
    "drumming", "fencing", "field hockey penalty", "floor gymnastics", 
    "catching a frisbee", "front crawl swimming", "golf swing", "haircut", 
    "hammering", "hammer throw", "handstand pushups", "handstand walking", 
    "head massage", "high jump", "horse racing", "horse riding", "hula hoop", 
    "ice dancing", "javelin throw", "juggling balls", "jumping jacks", 
    "jumping rope", "kayaking", "knitting", "long jump", "doing lunges", 
    "military parade", "mixing batter", "mopping floor", "using nunchucks", 
    "parallel bars gymnastics", "pizza tossing", "playing cello", "playing daf", 
    "playing dhol", "playing flute", "playing guitar", "playing piano", 
    "playing sitar", "playing tabla", "playing violin", "pole vaulting", 
    "pommel horse gymnastics", "doing pull ups", "punching", "doing push ups", 
    "rafting", "indoor rock climbing", "rope climbing", "rowing a boat", 
    "salsa spinning", "shaving beard", "shotput throw", "skateboarding", 
    "skiing", "riding a jetski", "sky diving", "soccer juggling", 
    "soccer penalty kick", "still rings gymnastics", "sumo wrestling", 
    "surfing", "swinging", "table tennis shot", "tai chi", "tennis swing", 
    "throwing discus", "trampoline jumping", "typing on keyboard", 
    "uneven bars gymnastics", "volleyball spiking", "walking with a dog", 
    "wall pushups", "writing on board", "playing with a yoyo",

    # General / Miscellaneous additions
    "person doing sign language", "person talking", "person standing", 
    "person sitting", "person taking a photo", "shopping", "laughing", 
    "crying", "beautiful landscape", "sunset", "ocean waves", "city street", 
    "abstract video", "screen recording", "news broadcast"
]

def classify_video(video_embedding):
    """
    Classifies a video based on its average CLIP embedding using zero-shot classification.
    """
    model, processor = get_clip_model()
    
    inputs = processor(text=LABELS, return_tensors="pt", padding=True).to(device)
    
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
        # Handle different transformer versions where output might be an object
        if hasattr(text_features, "pooler_output"):
            text_features = text_features.pooler_output
        elif not isinstance(text_features, torch.Tensor):
            # If it's a dictionary-like object (BaseModelOutputWithPooling)
            text_features = text_features[0] 
            
        text_features = text_features / torch.linalg.norm(text_features, dim=-1, keepdim=True)
    
    if isinstance(video_embedding, np.ndarray):
        video_embedding = torch.from_numpy(video_embedding).to(device).float()
    
    # Ensure video_embedding is also normalized
    video_embedding = video_embedding / torch.linalg.norm(video_embedding, dim=-1, keepdim=True)
    
    similarity = (100.0 * video_embedding @ text_features.T).softmax(dim=-1)
    top_idx = similarity.argmax().item()
    return LABELS[top_idx]