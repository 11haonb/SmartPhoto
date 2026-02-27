# SmartPhoto — AI 智能照片整理助手

<p align="center">
  <img src="docs/assets/banner.svg" alt="SmartPhoto" width="600">
</p>

<p align="center">
  <strong>上传照片，AI 自动分类、检测问题、挑选最佳</strong>
</p>

<p align="center">
  <a href="https://github.com/11haonb/SmartPhoto/actions"><img src="https://img.shields.io/github/actions/workflow/status/11haonb/SmartPhoto/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI"></a>
  <a href="https://github.com/11haonb/SmartPhoto/releases"><img src="https://img.shields.io/github/v/release/11haonb/SmartPhoto?include_prereleases&style=for-the-badge" alt="Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg?style=for-the-badge" alt="CC BY-NC-SA 4.0"></a>
  <a href="README_EN.md"><img src="https://img.shields.io/badge/English-README-green?style=for-the-badge" alt="English"></a>
</p>

<p align="center">
  Created by <a href="https://github.com/11haonb"><strong>liujinqi</strong></a>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#功能特性">功能特性</a> ·
  <a href="#技术架构">技术架构</a> ·
  <a href="#api-文档">API 文档</a> ·
  <a href="https://11haonb.github.io/SmartPhoto/">在线文档</a>
</p>

---

## 功能特性

SmartPhoto 是一个全栈 AI 照片整理系统，通过 5 阶段智能分析管道自动整理你的照片。

### 5 阶段 AI 分析管道

| 阶段 | 功能 | 说明 |
|------|------|------|
| 1 | **EXIF 时间线** | 自动提取拍摄时间、相机型号、GPS 位置，按日期分组 |
| 2 | **质量检测** | 识别模糊、过曝、欠曝、截图等问题照片 |
| 3 | **智能分类** | 人物(自拍/合照/人像)、风景(自然/建筑/城市)、美食、文档、截图 |
| 4 | **相似分组** | 基于 pHash 感知哈希找出重复/相似照片 |
| 5 | **最佳挑选** | 从每组相似照片中自动选出质量最好的一张 |

### 4 个 AI 引擎

| 引擎 | API Key | 准确度 | 适用场景 |
|------|---------|--------|----------|
| **本地离线** (Pillow + NumPy) | 不需要 | 基础 | 离线使用、零成本 |
| **HuggingFace** | 可选 | 中等 | 免费 3 万次/月 |
| **通义千问 VL** (阿里云) | 需要 | 高 | 国内访问快、中文优化 |
| **Claude Vision** (Anthropic) | 需要 | 最高 | 最精准的视觉分析 |

### 其他特性

- **手机号 + SMS 验证码登录** — 支持阿里云短信服务
- **批量上传** — 支持 JPG/PNG/HEIC/WebP，最大 10MB/张
- **自动生成缩略图和压缩版** — 300px 缩略图 + 1200px 压缩图
- **API Key 加密存储** — 用户的 AI 服务密钥使用 Fernet 对称加密
- **Celery 异步处理** — 后台执行 AI 分析，前端实时轮询进度
- **MinIO 对象存储** — 开发环境使用 MinIO，生产可切换 S3/COS

---

## 技术架构

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Flutter App    │     │   Web Demo      │     │  Swagger UI  │
│  (iOS/Android)  │     │  (手机外框测试)  │     │  /docs       │
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
│  (数据库)  │   │ (缓存/队列)│   │  (对象存储)   │
└───────────┘   └─────┬─────┘   └───────────────┘
                      │
               ┌──────┴──────┐
               │   Celery    │
               │  (异步任务)  │──→ AI Provider
               └─────────────┘    (Local/HF/Tongyi/Claude)
```

### 技术栈

| 层 | 技术 |
|---|------|
| **移动端** | Flutter 3.x + Dart, Provider, Dio, go_router |
| **Web 测试** | 原生 HTML/CSS/JS, 手机外框 CSS |
| **后端** | FastAPI 0.115, Python 3.12, Uvicorn |
| **数据库** | PostgreSQL 16, SQLAlchemy 2.0 (async), Alembic |
| **缓存/队列** | Redis 7, Celery 5.4 |
| **对象存储** | MinIO (dev) / S3 / COS (prod) |
| **AI** | Pillow, imagehash, NumPy, SciPy, Anthropic SDK, DashScope |
| **认证** | JWT (PyJWT), SMS (阿里云) |
| **部署** | Docker Compose, Nginx |

---

## 快速开始

### 前置要求

- Docker + Docker Compose
- Node.js 18+ (Web Demo)
- Git

### 1. 克隆项目

```bash
git clone git@github.com:11haonb/SmartPhoto.git
cd SmartPhoto
```

### 2. 配置环境变量

```bash
cd photo-organizer-backend
cp .env.example .env
# 按需修改 .env 中的配置
```

### 3. 启动后端

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

这会启动：
- **API 服务** (端口 28000) — 自动运行数据库迁移
- **Celery Worker** — 异步图片处理
- **PostgreSQL** (端口 25432)
- **Redis** (端口 26379)
- **MinIO** (端口 29000, 控制台 29001)

### 4. 启动 Web Demo

```bash
cd ../web-demo
node serve.js
```

### 5. 打开浏览器

```
http://localhost:3000
```

- 手机号: `13800138000`
- 验证码: `888888` (开发模式固定验证码)

---

## 项目结构

```
SmartPhoto/
├── photo-organizer-backend/       # FastAPI 后端
│   ├── app/
│   │   ├── ai/providers/          # 4 个 AI 引擎实现
│   │   ├── api/routes/            # REST API 路由 (auth/photos/organize/settings)
│   │   ├── core/                  # 配置、认证、短信、存储、加密
│   │   ├── models/                # SQLAlchemy 数据模型 (6 张表)
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── services/              # 图片处理服务
│   │   ├── tasks/                 # Celery 5 阶段处理管道
│   │   └── main.py
│   ├── alembic/versions/          # 数据库迁移
│   ├── docker-compose.dev.yml
│   └── Dockerfile
├── photo-organizer-flutter/       # Flutter 移动端
│   └── lib/
│       ├── screens/               # 8 个页面
│       ├── services/              # API + Auth 服务
│       ├── models/                # 数据模型
│       └── widgets/               # 可复用组件
├── web-demo/                      # Web 测试界面
│   ├── index.html                 # 手机外框入口
│   ├── css/                       # 样式 (phone-frame + app)
│   ├── js/                        # 模块 (api/auth/album/organize/results/app)
│   └── serve.js                   # Node.js 静态服务器
└── docs/                          # GitHub Pages 文档站
```

---

## API 文档

启动后端后访问 Swagger UI：`http://localhost:28000/docs`

### 端点概览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/v1/auth/send-code` | 发送短信验证码 |
| `POST` | `/api/v1/auth/login` | 手机号 + 验证码登录 |
| `POST` | `/api/v1/photos/batch` | 创建上传批次 |
| `POST` | `/api/v1/photos/upload` | 上传单张照片 |
| `GET` | `/api/v1/photos/batch/{id}` | 获取批次照片列表 |
| `GET` | `/api/v1/photos/{id}` | 获取照片详情 + 分析结果 |
| `DELETE` | `/api/v1/photos/{id}` | 删除照片 |
| `POST` | `/api/v1/organize/start` | 启动 AI 整理任务 |
| `GET` | `/api/v1/organize/status/{id}` | 查询处理进度 |
| `GET` | `/api/v1/organize/results/{id}` | 获取整理结果 (4 维度) |
| `GET` | `/api/v1/settings` | 获取用户 AI 配置 |
| `PUT` | `/api/v1/settings` | 更新 AI 引擎配置 |
| `GET` | `/api/v1/settings/ai-providers` | 获取可用 AI 引擎列表 |

---

## 开发指南

### 运行测试

```bash
cd photo-organizer-backend
docker compose -f docker-compose.dev.yml exec api pytest --cov=app
```

### 查看日志

```bash
# API 日志
docker compose -f docker-compose.dev.yml logs api -f

# Celery Worker 日志
docker compose -f docker-compose.dev.yml logs celery-worker -f
```

### 数据库管理

```bash
# 进入 PostgreSQL
docker compose -f docker-compose.dev.yml exec db psql -U postgres photo_organizer

# MinIO 控制台
http://localhost:29001  (minioadmin / minioadmin)
```

---

## 部署

### 生产环境

```bash
# 修改 .env 中的密钥和配置
docker compose -f docker-compose.prod.yml up -d
```

生产环境注意事项：
- 修改 `SECRET_KEY`, `JWT_SECRET_KEY`, `ENCRYPTION_KEY` 为强随机字符串
- 配置真实的阿里云 SMS 服务
- 使用阿里云 COS 或 AWS S3 替代 MinIO
- 配置 Nginx 反向代理和 HTTPS

---

## 许可证

[MIT License](LICENSE)
