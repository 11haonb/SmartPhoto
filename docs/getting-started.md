---
layout: default
title: 快速开始
---

# 快速开始

本指南帮你在 5 分钟内搭建 SmartPhoto 开发环境。

## 前置要求

| 工具 | 版本 | 用途 |
|------|------|------|
| Docker | 20+ | 容器化运行所有服务 |
| Docker Compose | v2+ | 服务编排 |
| Node.js | 18+ | Web Demo 静态服务器 |
| Git | 任意 | 代码管理 |

## Step 1：克隆项目

```bash
git clone git@github.com:11haonb/SmartPhoto.git
cd SmartPhoto
```

## Step 2：配置环境变量

```bash
cd photo-organizer-backend
cp .env.example .env
```

`.env` 文件中的关键配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_ENV` | development | 环境，开发模式下验证码固定为 888888 |
| `DATABASE_URL` | postgresql+asyncpg://... | 数据库连接 |
| `REDIS_URL` | redis://redis:6379/0 | Redis 连接 |
| `JWT_SECRET_KEY` | change-me | JWT 签名密钥，生产环境必须修改 |
| `STORAGE_ENDPOINT` | http://minio:9000 | 对象存储地址 |

## Step 3：启动后端

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

首次启动会：
1. 构建 Python 应用镜像
2. 拉取 PostgreSQL、Redis、MinIO 镜像
3. 自动运行 `alembic upgrade head` 创建数据库表
4. 初始化 MinIO bucket

启动后检查状态：

```bash
# 查看所有容器状态
docker compose -f docker-compose.dev.yml ps

# 检查 API 健康
curl http://localhost:28000/health
# 应返回: {"status":"ok"}

# 查看 Swagger 文档
open http://localhost:28000/docs
```

## Step 4：启动 Web Demo

```bash
cd ../web-demo
node serve.js
```

输出：

```
  SmartPhoto Web Demo
  -------------------
  Local:   http://localhost:3000
  Network: http://0.0.0.0:3000
```

## Step 5：测试

1. 浏览器打开 `http://localhost:3000`
2. 看到手机外框界面
3. 输入手机号 `13800138000`
4. 点击「获取验证码」
5. 输入验证码 `888888`（开发模式固定）
6. 点击「登录」→ 进入首页
7. 点击「选择照片开始整理」
8. 选择几张本地图片上传
9. 观察上传进度和 AI 分析进度
10. 查看整理结果（时间线 / 分类 / 问题图 / 最佳照片）

## 端口映射

| 服务 | 主机端口 | 容器端口 | 说明 |
|------|----------|----------|------|
| API | 28000 | 8000 | FastAPI 后端 |
| PostgreSQL | 25432 | 5432 | 数据库 |
| Redis | 26379 | 6379 | 缓存/消息队列 |
| MinIO | 29000 | 9000 | 对象存储 API |
| MinIO Console | 29001 | 9001 | MinIO 管理界面 |
| Web Demo | 3000 | 3000 | 测试界面 |

## 常见问题

### 端口冲突

如果主机已有 PostgreSQL/Redis 在运行，修改 `docker-compose.dev.yml` 中的端口映射。

### Docker 权限

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 国内 Docker 镜像拉取慢

在 `/etc/docker/daemon.json` 中添加镜像加速：

```json
{
  "registry-mirrors": ["https://docker.m.daocloud.io"]
}
```

然后重启 Docker：

```bash
sudo systemctl restart docker
```

---

下一步：[架构设计](architecture) | [API 文档](api-reference)
