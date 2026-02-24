FROM python:3.12-slim
WORKDIR /app
ENV HF_HOME=/app/.cache/huggingface

RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# CPU-only torch (avoids pulling ~2GB CUDA packages)
RUN pip install --no-cache-dir torch==2.5.1 \
    --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download CLIP model at build time (avoids cold-start latency)
RUN python -c "from transformers import CLIPModel, CLIPProcessor; \
    CLIPModel.from_pretrained('openai/clip-vit-base-patch32'); \
    CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')"

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
