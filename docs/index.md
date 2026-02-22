---
layout: default
title: SmartPhoto - AI 智能照片整理助手
---

<div style="text-align:center;margin-bottom:40px">
  <img src="assets/banner.svg" alt="SmartPhoto" width="500">
  <p style="font-size:18px;color:#666;margin-top:16px">
    上传照片，AI 自动分类、检测问题、挑选最佳
  </p>
  <p>
    <a href="https://github.com/11haonb/SmartPhoto">GitHub</a> ·
    <a href="getting-started">快速开始</a> ·
    <a href="api-reference">API 文档</a> ·
    <a href="architecture">架构设计</a> ·
    <a href="ai-providers">AI 引擎</a> ·
    <a href="web-demo">Web Demo</a>
  </p>
</div>

---

## 什么是 SmartPhoto？

SmartPhoto 是一个全栈 AI 照片整理系统。上传一批照片后，系统通过 **5 阶段 AI 分析管道** 自动完成：

1. **EXIF 时间线提取** — 读取拍摄时间、GPS 位置，按日期分组
2. **质量检测** — 识别模糊、过曝、欠曝、截图等问题照片
3. **智能分类** — 自动归类为人物、风景、美食、文档等
4. **相似分组** — 基于感知哈希找出重复/相似照片
5. **最佳挑选** — 从每组相似照片中选出质量最好的

## 技术栈

| 层 | 技术 |
|---|------|
| 移动端 | Flutter 3.x, Dart, Provider |
| 后端 | FastAPI, Python 3.12, Celery |
| 数据库 | PostgreSQL 16, Redis 7 |
| 存储 | MinIO / S3 / COS |
| AI 引擎 | Local, HuggingFace, 通义千问 VL, Claude Vision |
| 部署 | Docker Compose, Nginx |

## 页面导航

| 页面 | 说明 |
|------|------|
| [快速开始](getting-started) | 5 分钟搭建开发环境 |
| [架构设计](architecture) | 系统架构和数据流 |
| [API 文档](api-reference) | 全部 13 个 REST 端点 |
| [AI 引擎](ai-providers) | 4 个 AI 引擎的对比和配置 |
| [Web Demo](web-demo) | 手机外框测试界面使用指南 |
| [部署指南](deployment) | 生产环境部署清单 |

---

<div style="text-align:center;margin-top:40px;color:#999;font-size:13px">
  <p>Made with ❤️ by <a href="https://github.com/11haonb">11haonb</a></p>
</div>
