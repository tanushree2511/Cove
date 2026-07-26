# --- Frontend build stage ---
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Final image: cove + video Python services ---
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN python3 -m pip install --upgrade pip

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
# GPU-accelerated overrides for the CPU-default packages above
RUN pip3 install --no-cache-dir onnxruntime-gpu faiss-gpu

COPY cove/ ./cove/
COPY videoModules/ ./videoModules/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

EXPOSE 8000 8001 8501

CMD ["/bin/bash"]
