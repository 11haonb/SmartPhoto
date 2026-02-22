---
layout: default
title: API 文档
---

# API 文档

Base URL: `http://localhost:28000/api/v1`

交互式 Swagger 文档: `http://localhost:28000/docs`

## 认证

除了 `POST /auth/send-code`、`POST /auth/login`、`GET /settings/ai-providers` 外，所有接口都需要 JWT Bearer Token。

```
Authorization: Bearer <access_token>
```

---

## Auth 认证

### POST /auth/send-code

发送短信验证码。开发模式下验证码固定为 `888888`。

**Request:**
```json
{
  "phone": "13800138000"
}
```

**Response (200):**
```json
{
  "message": "Verification code sent"
}
```

**Errors:**
- `429` — 发送太频繁（60 秒限制）

---

### POST /auth/login

使用手机号 + 验证码登录，返回 JWT Token。

**Request:**
```json
{
  "phone": "13800138000",
  "code": "888888"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user_id": "cb137957-73ed-4809-b143-d877361e01ef"
}
```

**Errors:**
- `401` — 验证码错误或已过期

---

## Photos 照片管理

### POST /photos/batch

创建上传批次。

**Request:**
```json
{
  "total_photos": 10
}
```

**Response (200):**
```json
{
  "id": "534e4e46-85f0-4cab-bf11-c1f561399c57",
  "status": "uploading",
  "total_photos": 10,
  "uploaded_photos": 0,
  "created_at": "2026-02-22T15:36:03Z"
}
```

---

### POST /photos/upload

上传单张照片（multipart/form-data）。

**Request:**
- `batch_id`: string (UUID)
- `file`: binary (image/jpeg, image/png, image/heic, image/webp)

**Response (200):**
```json
{
  "id": "a1b2c3d4-...",
  "batch_id": "534e4e46-...",
  "original_filename": "IMG_0123.jpg",
  "thumbnail_url": "http://minio:9000/photo-organizer/thumbnails/..."
}
```

---

### GET /photos/batch/{batch_id}

获取批次内所有照片。

**Response (200):**
```json
[
  {
    "id": "a1b2c3d4-...",
    "original_filename": "IMG_0123.jpg",
    "thumbnail_url": "...",
    "compressed_url": "...",
    "mime_type": "image/jpeg",
    "file_size": 2048576,
    "width": 4032,
    "height": 3024,
    "taken_at": "2026-02-20T14:30:00Z",
    "camera_model": "iPhone 15 Pro",
    "gps_latitude": 39.9042,
    "gps_longitude": 116.4074,
    "created_at": "2026-02-22T15:36:10Z"
  }
]
```

---

### GET /photos/{photo_id}

获取单张照片详情 + AI 分析结果。

**Response (200):**
```json
{
  "photo": { "...PhotoResponse..." },
  "analysis": {
    "photo_id": "a1b2c3d4-...",
    "category": "landscape",
    "sub_category": "nature",
    "confidence": 0.92,
    "quality_score": 0.85,
    "is_blurry": false,
    "is_overexposed": false,
    "is_underexposed": false,
    "is_screenshot": false,
    "is_invalid": false,
    "invalid_reason": null,
    "similarity_group": "abc123",
    "is_best_in_group": true,
    "ai_provider": "LocalProvider",
    "analyzed_at": "2026-02-22T15:40:00Z"
  }
}
```

---

### DELETE /photos/{photo_id}

删除一张照片。

**Response:** `204 No Content`

---

## Organize 整理

### POST /organize/start

启动 AI 整理任务（触发 Celery 5 阶段管道）。

**Request:**
```json
{
  "batch_id": "534e4e46-..."
}
```

**Response (200):**
```json
{
  "task_id": "d0d23b7e-...",
  "status": "pending"
}
```

---

### GET /organize/status/{task_id}

查询处理进度。前端每 3 秒轮询一次。

**Response (200):**
```json
{
  "id": "d0d23b7e-...",
  "status": "running",
  "current_stage": 2,
  "total_stages": 5,
  "current_stage_name": "质量分析",
  "progress_percent": 35,
  "photos_processed": 3,
  "photos_total": 10,
  "error_message": null,
  "started_at": "2026-02-22T15:37:00Z",
  "completed_at": null
}
```

`status` 取值: `pending` → `running` → `completed` / `failed`

---

### GET /organize/results/{task_id}

获取整理结果（任务完成后可用）。返回 4 个维度的数据。

**Response (200):**
```json
{
  "task_id": "d0d23b7e-...",
  "timeline": [
    {
      "date": "2026-02-20",
      "photos": ["...PhotoResponse[]..."]
    }
  ],
  "categories": [
    {
      "category": "person",
      "sub_category": "selfie",
      "count": 3,
      "photos": ["...PhotoResponse[]..."]
    }
  ],
  "invalid_photos": [
    {
      "photo": {"...PhotoResponse..."},
      "analysis": {"...PhotoAnalysisResponse..."}
    }
  ],
  "similarity_groups": [
    {
      "group_id": "abc123",
      "photos": ["...PhotoDetailResponse[]..."],
      "best_photo_id": "a1b2c3d4-..."
    }
  ]
}
```

---

## Settings 设置

### GET /settings

获取用户当前 AI 配置和可用引擎列表。

### PUT /settings

更新 AI 引擎配置。

**Request:**
```json
{
  "ai_config": {
    "provider": "tongyi",
    "api_key": "sk-xxx...",
    "model": "qwen-vl-max"
  }
}
```

### GET /settings/ai-providers

获取所有可用 AI 引擎（无需认证）。

**Response (200):**
```json
[
  {
    "provider": "local",
    "name": "本地离线分析",
    "description": "使用 Pillow + NumPy 进行基础图像分析",
    "requires_api_key": false,
    "free_tier": "无限制",
    "accuracy": "基础"
  },
  {
    "provider": "tongyi",
    "name": "通义千问 VL",
    "description": "阿里云通义千问视觉语言模型",
    "requires_api_key": true,
    "free_tier": "有免费额度",
    "accuracy": "高"
  }
]
```

---

下一步：[AI 引擎](ai-providers) | [Web Demo](web-demo)
