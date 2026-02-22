---
layout: default
title: 部署指南
---

# 生产环境部署

## 前置清单

- [ ] 一台 Linux 服务器（推荐 2C4G 以上）
- [ ] Docker + Docker Compose 已安装
- [ ] 域名（可选，用于 HTTPS）
- [ ] 阿里云 SMS 服务已开通（用于短信登录）

## Step 1：准备配置

```bash
git clone git@github.com:11haonb/SmartPhoto.git
cd SmartPhoto/photo-organizer-backend
cp .env.example .env
```

编辑 `.env`，修改以下关键配置：

```bash
# 必须修改的安全配置
APP_ENV=production
DEBUG=false
SECRET_KEY=<随机32字符>
JWT_SECRET_KEY=<随机32字符>
ENCRYPTION_KEY=<32字节hex字符串>

# 数据库（使用强密码）
DATABASE_URL=postgresql+asyncpg://postgres:<强密码>@db:5432/photo_organizer

# SMS（阿里云真实配置）
SMS_ACCESS_KEY_ID=<你的阿里云AK>
SMS_ACCESS_KEY_SECRET=<你的阿里云SK>
SMS_SIGN_NAME=<你的短信签名>
SMS_TEMPLATE_CODE=<你的短信模板>

# 对象存储（生产可用 S3/COS）
STORAGE_ENDPOINT=http://minio:9000
STORAGE_ACCESS_KEY=<MinIO管理员用户名>
STORAGE_SECRET_KEY=<MinIO管理员密码>
```

生成随机密钥：

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Step 2：启动服务

```bash
docker compose -f docker-compose.prod.yml up -d
```

## Step 3：配置 Nginx（可选）

如果需要域名和 HTTPS：

```nginx
server {
    listen 80;
    server_name api.smartphoto.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name api.smartphoto.example.com;

    ssl_certificate /etc/letsencrypt/live/api.smartphoto.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.smartphoto.example.com/privkey.pem;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:28000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 安全清单

- [ ] 所有 Secret Key 已替换为随机强密码
- [ ] `APP_ENV=production`, `DEBUG=false`
- [ ] PostgreSQL 使用强密码
- [ ] MinIO 使用强密码
- [ ] SMS 服务已配置真实凭证
- [ ] Nginx 已配置 HTTPS
- [ ] 防火墙只开放 80/443 端口
- [ ] Docker 网络隔离，数据库/Redis 不暴露外部端口

## 监控

```bash
# 查看所有服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f celery-worker

# 进入数据库
docker compose -f docker-compose.prod.yml exec db psql -U postgres photo_organizer
```

## 备份

```bash
# 数据库备份
docker compose -f docker-compose.prod.yml exec db \
  pg_dump -U postgres photo_organizer > backup_$(date +%Y%m%d).sql

# MinIO 数据备份
docker compose -f docker-compose.prod.yml exec minio \
  mc mirror /data /backup
```

---

返回：[快速开始](getting-started) | [首页](./)
