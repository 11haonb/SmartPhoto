# SmartPhoto — AI-Powered Photo Organizer

<p align="center">
  <img src="docs/assets/banner.svg" alt="SmartPhoto" width="600">
</p>

<p align="center">
  <strong>Upload photos, let AI classify, detect issues, and pick the best</strong>
</p>

<p align="center">
  <a href="https://github.com/11haonb/SmartPhoto/actions"><img src="https://img.shields.io/github/actions/workflow/status/11haonb/SmartPhoto/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"></a>
  <a href="https://github.com/11haonb/SmartPhoto/releases"><img src="https://img.shields.io/github/v/release/11haonb/SmartPhoto?include_prereleases&style=for-the-badge" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="README.md"><img src="https://img.shields.io/badge/中文-README-green?style=for-the-badge" alt="中文"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#features">Features</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#api-reference">API Reference</a> ·
  <a href="https://11haonb.github.io/SmartPhoto/">Documentation</a>
</p>

---

## Features

SmartPhoto is a full-stack AI photo organization system with a 5-stage intelligent analysis pipeline.

### 5-Stage AI Pipeline

| Stage | Feature | Description |
|-------|---------|-------------|
| 1 | **EXIF Timeline** | Extract shooting date, camera model, GPS coordinates; group by date |
| 2 | **Quality Detection** | Identify blurry, overexposed, underexposed, and screenshot images |
| 3 | **Smart Classification** | Person (selfie/group/portrait), Landscape (nature/building/city), Food, Document, Screenshot |
| 4 | **Similarity Grouping** | Find duplicate/similar photos using perceptual hashing (pHash) |
| 5 | **Best Pick** | Automatically select the highest quality photo from each similar group |

### 4 AI Engines

| Engine | API Key | Accuracy | Best For |
|--------|---------|----------|----------|
| **Local Offline** (Pillow + NumPy) | Not required | Basic | Zero-cost, offline use |
| **HuggingFace** | Optional | Medium | Free 30K calls/month |
| **Tongyi Qwen VL** (Alibaba Cloud) | Required | High | Fast in China, Chinese optimized |
| **Claude Vision** (Anthropic) | Required | Highest | Most accurate visual analysis |

### Additional Features

- **Phone + SMS Login** — Aliyun SMS service integration
- **Batch Upload** — JPG/PNG/HEIC/WebP support, max 10MB per image
- **Auto Thumbnails** — 300px thumbnails + 1200px compressed versions
- **Encrypted API Keys** — User AI keys stored with Fernet symmetric encryption
- **Async Processing** — Celery workers for background AI analysis with real-time progress
- **Object Storage** — MinIO (dev) / S3 / COS (prod)

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Flutter App    │     │   Web Demo      │     │  Swagger UI  │
│  (iOS/Android)  │     │  (Phone Frame)  │     │  /docs       │
└────────┬────────┘     └────────┬────────┘     └──────┬───────┘
         │                       │                      │
         └───────────────┬───────┴──────────────────────┘
                         │ HTTP/REST
                ┌────────┴────────┐
                │   FastAPI       │
                │   (Uvicorn)     │
                └────────┬────────┘
         ┌───────────────┼───────────────┐
         │               │               │
┌────────┴──┐   ┌────────┴──┐   ┌────────┴──────┐
│PostgreSQL │   │   Redis   │   │    MinIO      │
│ (Database)│   │(Cache/MQ) │   │(Object Store) │
└───────────┘   └─────┬─────┘   └───────────────┘
                      │
               ┌──────┴──────┐
               │   Celery    │
               │  (Workers)  │──→ AI Provider
               └─────────────┘    (Local/HF/Tongyi/Claude)
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Mobile** | Flutter 3.x + Dart, Provider, Dio, go_router |
| **Web Demo** | Vanilla HTML/CSS/JS, iPhone-style CSS frame |
| **Backend** | FastAPI 0.115, Python 3.12, Uvicorn |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 (async), Alembic |
| **Cache/Queue** | Redis 7, Celery 5.4 |
| **Storage** | MinIO (dev) / S3 / COS (prod) |
| **AI** | Pillow, imagehash, NumPy, SciPy, Anthropic SDK, DashScope |
| **Auth** | JWT (PyJWT), SMS (Aliyun) |
| **Deploy** | Docker Compose, Nginx |

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Node.js 18+ (for Web Demo)
- Git

### 1. Clone

```bash
git clone git@github.com:11haonb/SmartPhoto.git
cd SmartPhoto
```

### 2. Configure

```bash
cd photo-organizer-backend
cp .env.example .env
```

### 3. Start Backend

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

This starts:
- **API Server** (port 28000) — auto-runs database migrations
- **Celery Worker** — background photo processing
- **PostgreSQL** (port 25432)
- **Redis** (port 26379)
- **MinIO** (port 29000, console 29001)

### 4. Start Web Demo

```bash
cd ../web-demo
node serve.js
```

### 5. Open Browser

```
http://localhost:3000
```

- Phone: `13800138000`
- Code: `888888` (fixed in dev mode)

---

## Project Structure

```
SmartPhoto/
├── photo-organizer-backend/       # FastAPI backend
│   ├── app/
│   │   ├── ai/providers/          # 4 AI engine implementations
│   │   ├── api/routes/            # REST API (auth/photos/organize/settings)
│   │   ├── core/                  # Config, auth, SMS, storage, encryption
│   │   ├── models/                # SQLAlchemy models (6 tables)
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── services/              # Photo processing service
│   │   ├── tasks/                 # Celery 5-stage pipeline
│   │   └── main.py
│   ├── alembic/versions/          # Database migrations
│   ├── docker-compose.dev.yml
│   └── Dockerfile
├── photo-organizer-flutter/       # Flutter mobile app
│   └── lib/
│       ├── screens/               # 8 screens
│       ├── services/              # API + Auth services
│       ├── models/                # Data models
│       └── widgets/               # Reusable components
├── web-demo/                      # Web test interface
│   ├── index.html                 # Phone-frame entry
│   ├── css/                       # Styles (phone-frame + app)
│   ├── js/                        # Modules (api/auth/album/organize/results/app)
│   └── serve.js                   # Node.js static server
└── docs/                          # GitHub Pages documentation
```

---

## API Reference

Swagger UI available at `http://localhost:28000/docs` when backend is running.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/auth/send-code` | Send SMS verification code |
| `POST` | `/api/v1/auth/login` | Login with phone + code |
| `POST` | `/api/v1/photos/batch` | Create upload batch |
| `POST` | `/api/v1/photos/upload` | Upload a single photo |
| `GET` | `/api/v1/photos/batch/{id}` | List photos in batch |
| `GET` | `/api/v1/photos/{id}` | Get photo detail + analysis |
| `DELETE` | `/api/v1/photos/{id}` | Delete a photo |
| `POST` | `/api/v1/organize/start` | Start AI organize task |
| `GET` | `/api/v1/organize/status/{id}` | Poll processing progress |
| `GET` | `/api/v1/organize/results/{id}` | Get organize results (4 views) |
| `GET` | `/api/v1/settings` | Get user AI config |
| `PUT` | `/api/v1/settings` | Update AI engine config |
| `GET` | `/api/v1/settings/ai-providers` | List available AI engines |

---

## Development

### Run Tests

```bash
cd photo-organizer-backend
docker compose -f docker-compose.dev.yml exec api pytest --cov=app
```

### View Logs

```bash
docker compose -f docker-compose.dev.yml logs api -f
docker compose -f docker-compose.dev.yml logs celery-worker -f
```

### Database Access

```bash
docker compose -f docker-compose.dev.yml exec db psql -U postgres photo_organizer
```

---

## Deployment

### Production

```bash
docker compose -f docker-compose.prod.yml up -d
```

Production checklist:
- Set strong random values for `SECRET_KEY`, `JWT_SECRET_KEY`, `ENCRYPTION_KEY`
- Configure real Aliyun SMS credentials
- Replace MinIO with S3 or COS
- Set up Nginx reverse proxy with HTTPS

---

## License

[MIT License](LICENSE)
