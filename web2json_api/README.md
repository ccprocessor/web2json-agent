# Web2JSON Agent - 简化版 Web API

## 简介

这是一个**极简版**的 Web API，专注于核心功能：
1. **输入HTML** - 粘贴或提供HTML内容
2. **定义字段** - 手动定义需要抽取的字段
3. **生成XPath** - 点击按钮，AI自动生成XPath表达式

## 快速开始

### 1. 启动服务

```bash
# 方式1: 直接运行（推荐）
python -m web2json_api.main

# 方式2: 使用 uvicorn
uvicorn web2json_api.main:app --reload --port 8000
```

服务启动后访问：**http://localhost:8000/api/docs**

### 2. API端点

#### 唯一核心端点

```
POST /api/xpath/generate
```

**功能**：接收HTML和字段定义，返回生成的XPath

## 使用示例

### 请求格式

```json
{
  "html_content": "<html>...</html>",
  "fields": [
    {
      "name": "price",
      "description": "Product price",
      "field_type": "string"
    }
  ]
}
```

### 完整示例

```bash
curl -X POST "http://localhost:8000/api/xpath/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Test Product Page</title>\n</head>\n<body>\n    <h1 class=\"product-title\">Amazing Product</h1>\n    <div class=\"price-container\">\n        <span class=\"price\">$99.99</span>\n    </div>\n    <p class=\"description\">This is a great product with many features.</p>\n</body>\n</html>",
    "fields": [
      {
        "name": "title",
        "description": "Product title",
        "field_type": "string"
      },
      {
        "name": "price",
        "description": "Product price",
        "field_type": "string"
      },
      {
        "name": "description",
        "description": "Product description",
        "field_type": "string"
      }
    ]
  }'
```

### 响应示例

```json
{
  "success": true,
  "fields": [
    {
      "name": "title",
      "description": "Product title",
      "field_type": "string",
      "xpath": "//h1[@class='product-title']/text()",
      "value_sample": ["Amazing Product"]
    },
    {
      "name": "price",
      "description": "Product price",
      "field_type": "string",
      "xpath": "//div[@class='price-container']/span[@class='price']/text()",
      "value_sample": ["$99.99"]
    },
    {
      "name": "description",
      "description": "Product description",
      "field_type": "string",
      "xpath": "//p[@class='description']/text()",
      "value_sample": ["This is a great product with many features."]
    }
  ],
  "error": null,
  "message": "Successfully generated XPath for 3 field(s)"
}
```

## 字段说明

### 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `html_content` | string | ✅ | HTML内容 |
| `fields` | array | ✅ | 字段定义列表 |
| `fields[].name` | string | ✅ | 字段名 |
| `fields[].description` | string | ❌ | 字段描述（可选，但建议填写以提高准确率） |
| `fields[].field_type` | string | ❌ | 字段类型，默认"string"。可选值：string, int, float, bool, array |

### 响应参数

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 是否成功 |
| `fields` | array | 包含XPath的字段列表 |
| `fields[].name` | string | 字段名 |
| `fields[].xpath` | string | **生成的XPath表达式** |
| `fields[].value_sample` | array | 从HTML中提取的示例值 |
| `error` | string | 错误信息（如有） |
| `message` | string | 提示信息 |

## 核心特性

### ✅ 完美集成现有Agent

```python
# 内部调用 web2json agent 的核心函数
from web2json.tools.schema_extraction import enrich_schema_with_xpath

enriched_schema = enrich_schema_with_xpath.invoke({
    "schema_template": schema_template,
    "html_content": html_content
})
```

### ✅ 无状态设计

- 不需要session管理
- 不需要文件上传
- 每次请求独立处理

### ✅ 简单直接

- 只有1个API端点
- 请求-响应模式
- 易于前端集成

## 前端集成示例

### JavaScript/Fetch

```javascript
async function generateXPath(htmlContent, fields) {
  const response = await fetch('http://localhost:8000/api/xpath/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      html_content: htmlContent,
      fields: fields
    })
  });

  const result = await response.json();
  return result;
}

// 使用示例
const result = await generateXPath(
  '<html>...</html>',
  [
    { name: 'title', description: 'Page title', field_type: 'string' },
    { name: 'price', description: 'Product price', field_type: 'string' }
  ]
);

console.log(result.fields); // 包含生成的XPath
```

### Vue 3 示例

```vue
<script setup>
import { ref } from 'vue';
import axios from 'axios';

const htmlContent = ref('');
const fields = ref([
  { name: '', description: '', field_type: 'string' }
]);
const results = ref(null);
const loading = ref(false);

async function generateXPath() {
  loading.value = true;
  try {
    const response = await axios.post('http://localhost:8000/api/xpath/generate', {
      html_content: htmlContent.value,
      fields: fields.value
    });
    results.value = response.data;
  } catch (error) {
    console.error('Failed to generate XPath:', error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div>
    <textarea v-model="htmlContent" placeholder="粘贴HTML内容"></textarea>

    <div v-for="(field, index) in fields" :key="index">
      <input v-model="field.name" placeholder="字段名" />
      <input v-model="field.description" placeholder="描述（可选）" />
    </div>

    <button @click="generateXPath" :disabled="loading">
      {{ loading ? '生成中...' : '生成XPath' }}
    </button>

    <div v-if="results">
      <div v-for="field in results.fields" :key="field.name">
        <h4>{{ field.name }}</h4>
        <code>{{ field.xpath }}</code>
        <p>示例值: {{ field.value_sample.join(', ') }}</p>
      </div>
    </div>
  </div>
</template>
```

## 架构说明

```
web2json_api/
├── main.py                    # FastAPI 应用入口
├── models/
│   ├── field.py              # 字段模型（FieldInput, FieldOutput）
│   └── xpath.py              # XPath请求/响应模型
├── routers/
│   └── xpath.py              # XPath生成端点
└── services/
    └── xpath_service.py      # XPath生成服务（对接agent）
```

**核心流程：**

1. 前端发送 HTML + 字段定义
2. `xpath_service.py` 转换为 agent schema格式
3. 调用 `enrich_schema_with_xpath()` 生成XPath
4. 转换回前端格式并返回

## 错误处理

如果请求失败，响应格式：

```json
{
  "success": false,
  "fields": [],
  "error": "错误详情",
  "message": "Failed to generate XPath"
}
```

## 依赖

- FastAPI 0.109.0
- Uvicorn 0.27.0
- web2json agent (核心)
- 其他依赖见 `pyproject.toml`

## 配置

确保 `.env` 文件包含必要的API配置：

```bash
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1
DEFAULT_MODEL=claude-sonnet-4-5-20250929
```

## 下一步

完成后端后，接下来实现前端：

1. Vue 3 项目初始化
2. HTML输入组件
3. 字段定义组件（可添加/删除）
4. XPath展示组件
5. 与后端API集成

---

**简洁高效，开箱即用！** 🚀
