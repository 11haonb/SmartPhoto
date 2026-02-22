---
layout: default
title: 架构设计
---

# 架构设计

## 系统架构

```
┌─────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Flutter App    │     │   Web Demo      │     │  Swagger UI  │
│  (iOS/Android)  │     │  (手机外框测试)  │     │  /docs       │
└────────┬────────┘     └────────┬────────┘     └──────┬───────┘
         │                       │                      │
         └───────────────┬───────┴──────────────────────┘
                         │ HTTP/REST (JSON)
                ┌────────┴────────┐
                │   FastAPI       │
                │   + CORS        │
                │   + JWT Auth    │
                └────────┬────────┘
         ┌───────────────┼───────────────┐
         │               │               │
┌────────┴──┐   ┌────────┴──┐   ┌────────┴──────┐
│PostgreSQL │   │   Redis   │   │    MinIO      │
│ 6 张表    │   │ SMS 验证码 │   │ 原图/缩略图   │
│ 用户/照片  │   │ 频率限制   │   │ 压缩图        │
│ 分析结果   │   │ Celery MQ │   │              │
└───────────┘   └─────┬─────┘   └───────────────┘
                      │
               ┌──────┴──────┐
               │   Celery    │
               │  Worker(s)  │
               └──────┬──────┘
                      │
            ┌─────────┼─────────┐
            │         │         │
      ┌─────┴──┐ ┌────┴───┐ ┌──┴──────┐
      │ Local  │ │ Tongyi │ │ Claude  │
      │Provider│ │ Qwen VL│ │ Vision  │
      └────────┘ └────────┘ └─────────┘
```

## 数据模型 (6 张表)

```
┌──────────┐       ┌──────────────┐
│  users   │───┐   │  ai_configs  │
│          │   └──→│  (per user)  │
└────┬─────┘       └──────────────┘
     │
     ├──→ ┌──────────┐       ┌────────────┐
     │    │ batches  │───┐   │   photos   │
     │    │          │   └──→│            │
     │    └──────────┘       └─────┬──────┘
     │                             │
     │                    ┌────────┴────────┐
     │                    │ photo_analyses  │
     │                    │ (1:1 with photo)│
     │                    └─────────────────┘
     │
     └──→ ┌───────────────────┐
          │ processing_tasks  │
          │ (Celery tracking) │
          └───────────────────┘
```

### 表结构详情

#### users
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| phone | VARCHAR(20) | 手机号，唯一索引 |
| nickname | VARCHAR(128) | 昵称 |
| avatar_url | VARCHAR(512) | 头像 URL |
| created_at / updated_at | TIMESTAMPTZ | 时间戳 |

#### photos
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| batch_id | UUID | 所属批次 FK |
| storage_path | VARCHAR(512) | MinIO 原图路径 |
| thumbnail_path | VARCHAR(512) | 缩略图路径 |
| taken_at | TIMESTAMPTZ | EXIF 拍摄时间 |
| camera_model | VARCHAR(128) | 相机型号 |
| gps_latitude / longitude | FLOAT | GPS 坐标 |
| phash | VARCHAR(64) | 感知哈希值，用于相似分组 |

#### photo_analyses
| 字段 | 类型 | 说明 |
|------|------|------|
| category | VARCHAR(50) | 分类：person/landscape/food/document/screenshot/other |
| sub_category | VARCHAR(50) | 子分类：portrait/group/selfie/building/nature/city |
| quality_score | FLOAT | 质量评分 0-1 |
| is_blurry | BOOLEAN | 是否模糊 |
| is_overexposed | BOOLEAN | 是否过曝 |
| is_underexposed | BOOLEAN | 是否欠曝 |
| is_screenshot | BOOLEAN | 是否截图 |
| similarity_group | VARCHAR(64) | 相似组 ID |
| is_best_in_group | BOOLEAN | 是否为组内最佳 |

## 5 阶段处理管道

```
用户点击「开始整理」
        │
        ▼
┌─────────────────────────────────────────────────┐
│              Celery Task: run_pipeline           │
│                                                  │
│  Stage 1: EXIF 提取                              │
│  ├─ 读取每张照片的 EXIF 元数据                     │
│  ├─ 提取: taken_at, camera_model, gps, orientation│
│  ├─ 计算 pHash 感知哈希值                         │
│  └─ 更新 photos 表                               │
│                                                  │
│  Stage 2: 质量分析                                │
│  ├─ AI Provider.assess_quality(image_bytes)       │
│  ├─ 输出: quality_score, is_blurry, is_overexposed│
│  └─ 创建 photo_analyses 记录                      │
│                                                  │
│  Stage 3: 图片分类                                │
│  ├─ AI Provider.classify(image_bytes)             │
│  ├─ 输出: category, sub_category, confidence      │
│  └─ 更新 photo_analyses                          │
│                                                  │
│  Stage 4: 相似度分组                              │
│  ├─ 比较所有照片的 pHash 值                        │
│  ├─ 汉明距离 ≤ 10 归为同组                        │
│  └─ 更新 similarity_group 字段                    │
│                                                  │
│  Stage 5: 最佳挑选                                │
│  ├─ AI Provider.pick_best(group_images)           │
│  ├─ 标记每组最佳照片 is_best_in_group = true       │
│  └─ 更新 processing_task 状态为 completed          │
└─────────────────────────────────────────────────┘
```

## 请求流程

### 登录流程

```
Client              API                 Redis
  │── POST /send-code ──→│                  │
  │                      │── SETEX code ───→│
  │                      │── SETEX rate ───→│
  │←── 200 ──────────────│                  │
  │                      │                  │
  │── POST /login ──────→│                  │
  │                      │── GET code ─────→│
  │                      │←── "888888" ─────│
  │                      │── DELETE code ──→│
  │←── {access_token} ──│                  │
```

### 上传 + 整理流程

```
Client              API              MinIO          Celery        DB
  │── POST /batch ──→│                 │               │           │
  │←── {batch_id} ──│                 │               │           │
  │                  │                 │               │           │
  │── POST /upload ─→│── PUT object ──→│               │           │
  │                  │                 │               │           │
  │←── {photo_id} ──│                 │               │           │
  │  ... repeat ...  │                 │               │           │
  │                  │                 │               │           │
  │── POST /start ──→│                 │               │           │
  │                  │── send_task ────────────────────→│           │
  │←── {task_id} ───│                 │               │           │
  │                  │                 │               │──→ 5 stages│
  │── GET /status ──→│                 │               │           │
  │←── {progress} ──│←────────────────────────────────│           │
  │  ... poll 3s ... │                 │               │           │
  │                  │                 │               │           │
  │── GET /results ─→│                 │               │           │
  │←── {timeline,categories,issues,groups} ───────────────────────│
```

---

下一步：[API 文档](api-reference) | [AI 引擎](ai-providers)
