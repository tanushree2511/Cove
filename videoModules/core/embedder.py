import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model and processor (will use local cache if already downloaded)
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

model.eval()

def encode_image(frame):
    image = Image.fromarray(frame)
    inputs = processor(images=image, return_tensors="pt")
    pixel_values = inputs["pixel_values"].to(device)

    with torch.no_grad():
        vision_outputs = model.vision_model(pixel_values=pixel_values)
        pooled_output = vision_outputs.pooler_output
        image_features = model.visual_projection(pooled_output)

    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    return image_features.cpu().numpy()[0]

def encode_images_batch(frames, batch_size=32):
    """Encodes a batch of frames efficiently on the GPU."""
    all_embeddings = []
    for i in range(0, len(frames), batch_size):
        batch = frames[i : i + batch_size]
        images = [Image.fromarray(f) for f in batch]
        
        inputs = processor(images=images, return_tensors="pt", padding=True)
        pixel_values = inputs["pixel_values"].to(device)

        with torch.no_grad():
            vision_outputs = model.vision_model(pixel_values=pixel_values)
            pooled_output = vision_outputs.pooler_output
            image_features = model.visual_projection(pooled_output)

        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        all_embeddings.append(image_features.cpu().numpy())
    
    return np.concatenate(all_embeddings, axis=0)

def encode_text(text):
    inputs = processor(text=[text], return_tensors="pt", padding=True)
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs["attention_mask"].to(device)

    with torch.no_grad():
        text_outputs = model.text_model(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = text_outputs.pooler_output
        text_features = model.text_projection(pooled_output)

    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    return text_features.cpu().numpy()[0]

def generate_video_embedding(frames):
    if len(frames) == 0:
        raise ValueError("No frames extracted from video")
    
    # Use batch encoding for better performance
    embeddings = encode_images_batch(frames)
    video_embedding = np.mean(embeddings, axis=0)
    video_embedding = video_embedding / np.linalg.norm(video_embedding)
    return video_embedding