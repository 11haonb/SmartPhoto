---
layout: default
title: AI 引擎
---

# AI 引擎

SmartPhoto 支持 4 个 AI 引擎，通过工厂模式统一接口，用户可在设置页面自由切换。

## 引擎对比

| 特性 | Local | HuggingFace | 通义千问 VL | Claude Vision |
|------|-------|-------------|------------|---------------|
| API Key | 不需要 | 可选 | 必需 | 必需 |
| 网络 | 离线 | 需要 | 需要 | 需要 |
| 准确度 | 基础 | 中等 | 高 | 最高 |
| 成本 | 免费 | 免费额度 | 按量计费 | 按量计费 |
| 分类 | ✅ | ✅ | ✅ | ✅ |
| 质量检测 | ✅ | ❌ | ✅ | ✅ |
| 最佳挑选 | ✅ | ❌ | ✅ | ✅ |
| 中文优化 | - | - | ✅ | ✅ |

## 1. 本地离线引擎 (Local)

**无需 API Key，无需网络。**

使用 Pillow + NumPy + SciPy 进行基于启发式规则的图像分析：

- **分类**: 基于图像分辨率、宽高比、颜色直方图分布
- **模糊检测**: 拉普拉斯算子方差法
- **过曝检测**: 亮度直方图高区占比
- **欠曝检测**: 亮度直方图低区占比
- **截图检测**: 检测状态栏、导航栏等 UI 元素特征
- **相似分组**: pHash 感知哈希 + 汉明距离
- **最佳挑选**: 综合清晰度、曝光、色彩评分

适用场景：
- 不想使用云服务
- 离线环境
- 大批量处理（无 API 调用限制）

## 2. HuggingFace

使用 HuggingFace Inference API（免费层 30K 次/月）。

- **模型**: Salesforce/blip2-opt-2.7b
- **能力**: 图像分类、内容理解
- **限制**: 不支持质量检测和最佳挑选

配置：
```
Provider: huggingface
API Key: 可选（不填使用匿名额度）
```

## 3. 通义千问 VL (Tongyi Qwen)

阿里云通义千问视觉语言模型。

- **模型**: qwen-vl-max
- **能力**: 全功能（分类 + 质量检测 + 最佳挑选）
- **优势**: 国内网络访问快，中文提示优化
- **成本**: 有免费额度，超出按 token 计费

配置：
```
Provider: tongyi
API Key: 从阿里云 DashScope 控制台获取
Model: qwen-vl-max (默认)
```

获取 API Key：
1. 访问 [DashScope 控制台](https://dashscope.console.aliyun.com/)
2. 开通模型服务
3. 创建 API Key

## 4. Claude Vision

Anthropic Claude 视觉分析，准确度最高。

- **模型**: claude-sonnet-4-20250514
- **能力**: 全功能，最精准的视觉理解
- **优势**: 复杂场景理解能力最强
- **成本**: 按 token 计费

配置：
```
Provider: claude
API Key: 从 Anthropic Console 获取
Model: claude-sonnet-4-20250514 (默认)
```

## 切换 AI 引擎

### 通过 Web Demo

1. 点击底部「设置」Tab
2. 选择想要使用的 AI 引擎
3. 如需 API Key，在输入框中填写
4. 点击「保存设置」

### 通过 API

```bash
curl -X PUT http://localhost:28000/api/v1/settings \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "ai_config": {
      "provider": "tongyi",
      "api_key": "sk-xxx",
      "model": "qwen-vl-max"
    }
  }'
```

## 安全性

用户的 API Key 使用 Fernet 对称加密存储在数据库中，加密密钥由 `ENCRYPTION_KEY` 环境变量控制。明文 API Key 不会被持久化存储。

---

下一步：[Web Demo](web-demo) | [部署指南](deployment)
