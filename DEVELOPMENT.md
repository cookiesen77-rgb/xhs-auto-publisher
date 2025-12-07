# 开发文档

本文档面向二次开发者，介绍项目架构、核心模块和扩展方法。

## 项目架构

```
xhs-auto-publisher/
├── workflow.py              # 主入口，串联所有模块
├── modules/
│   ├── content_generator.py # 文案生成模块
│   ├── image_fetcher.py     # 图片生成模块
│   └── xhs_playwright.py    # 自动发布模块
├── output/                  # 草稿JSON存储
└── images/                  # 生成图片存储
```

## 核心模块详解

### 1. 文案生成模块 (`modules/content_generator.py`)

**功能**: 调用硅基流动API生成小红书风格文案

**核心类**: `ContentGenerator`

```python
from content_generator import ContentGenerator

generator = ContentGenerator()
content = generator.search_and_generate("主题")
# 返回: {title, content, tags, image_keywords, created_at, original_topic}
```

**关键配置**:
- `SILICONFLOW_API_KEY` - API密钥
- `SILICONFLOW_MODEL` - 模型名称

**扩展点**:
- 修改 `prompt` 模板自定义文案风格
- 调整 `max_tokens`、`temperature` 参数
- 添加更多字段到返回结果

**Prompt模板位置**: `search_and_generate()` 方法内

```python
prompt = f"""基于以下主题生成小红书风格的文案：
主题：{topic}
请生成：
1. 吸引人的标题（带emoji，20字以内）
2. 正文内容（200-500字，分段，带emoji）
3. 5-10个相关话题标签
4. 3-5个建议的图片关键词
...
"""
```

---

### 2. 图片生成模块 (`modules/image_fetcher.py`)

**功能**: 调用硅基流动API生成配图

**核心类**: `ImageFetcher`

```python
from image_fetcher import ImageFetcher

fetcher = ImageFetcher("./images")
images = fetcher.search_and_download(["关键词1", "关键词2"], count=3)
# 返回: ["/path/to/image1.jpg", "/path/to/image2.jpg", ...]
```

**关键配置**:
- `SILICONFLOW_IMAGE_API_KEY` - 图片API密钥（可选，默认用通用key）
- `SILICONFLOW_IMAGE_MODEL` - 图片模型

**支持的模型**:
| 模型 | 类型 | 说明 |
|------|------|------|
| `Kwai-Kolors/Kolors` | 纯文生图 | 推荐，效果好 |
| `Qwen/Qwen-Image` | 纯文生图 | 通用 |
| `Qwen/Qwen-Image-Edit` | 图片编辑 | 需要参考图 |

**扩展点**:
- `_enhance_prompt()` - 修改prompt增强逻辑
- `_get_reference_image()` - 自定义参考图来源
- 添加更多图片源作为备用

**备用方案**: 当AI生图失败时，自动使用 Picsum 随机图片

---

### 3. 自动发布模块 (`modules/xhs_playwright.py`)

**功能**: 使用Playwright自动化发布到小红书

**核心类**: `XHSPublisher`

```python
from xhs_playwright import XHSPublisher
import asyncio

async def publish():
    publisher = XHSPublisher(headless=False)
    await publisher.init_browser()
    
    result = await publisher.publish(
        title="标题",
        content="正文",
        images=["image1.jpg", "image2.jpg"],
        tags=["标签1", "标签2"]
    )
    
    await publisher.close()
    return result

asyncio.run(publish())
```

**关键方法**:
| 方法 | 功能 |
|------|------|
| `init_browser()` | 初始化浏览器（持久化登录状态） |
| `check_login()` | 检查登录状态 |
| `wait_for_login()` | 等待用户手动登录 |
| `publish()` | 执行发布流程 |
| `close()` | 关闭浏览器 |

**页面元素选择器**（可能需要根据小红书更新调整）:

```python
# 标题输入框
'input[placeholder*="标题"], input.d-text'

# 正文编辑器（ProseMirror富文本）
'.tiptap.ProseMirror, div[contenteditable="true"]'

# 发布按钮
'button.publishBtn, button:has-text("发布")'

# 文件上传
'input[type="file"]'
```

**扩展点**:
- 修改选择器适配页面变化
- 添加更多发布选项（定时发布、可见范围等）
- 添加发布后验证逻辑

**登录状态存储**: `~/.xhs_browser_data/`

---

## 数据流

```
用户输入主题
    ↓
ContentGenerator.search_and_generate()
    ↓ 调用硅基流动API
返回: {title, content, tags, image_keywords}
    ↓
ImageFetcher.search_and_download(image_keywords)
    ↓ 调用硅基流动图片API
返回: [image_paths]
    ↓
XHSPublisher.publish(title, content, images, tags)
    ↓ Playwright自动化
发布成功
```

## API调用格式

### 文案生成 (Chat Completions)

```bash
POST https://api.siliconflow.cn/v1/chat/completions
Headers:
  Authorization: Bearer <API_KEY>
  Content-Type: application/json

Body:
{
  "model": "deepseek-ai/DeepSeek-R1",
  "messages": [{"role": "user", "content": "prompt"}],
  "max_tokens": 2000,
  "temperature": 0.7
}
```

### 图片生成 (Images Generations)

```bash
POST https://api.siliconflow.cn/v1/images/generations
Headers:
  Authorization: Bearer <API_KEY>
  Content-Type: application/json

Body:
{
  "model": "Kwai-Kolors/Kolors",
  "prompt": "图片描述",
  "image_size": "1024x1024",
  "num_inference_steps": 20,
  "guidance_scale": 7.5,
  "seed": 随机数
}
```

## 扩展开发示例

### 1. 添加新的文案风格

```python
# content_generator.py

def search_and_generate(self, topic: str, style: str = "default") -> dict:
    styles = {
        "default": "小红书风格，活泼可爱",
        "professional": "专业严谨，数据支撑",
        "story": "故事性强，情感共鸣"
    }
    
    prompt = f"""基于以下主题生成{styles[style]}的文案：
    主题：{topic}
    ...
    """
```

### 2. 添加多平台支持

```python
# 新建 modules/weibo_publisher.py

class WeiboPublisher:
    def __init__(self):
        self.url = "https://weibo.com"
    
    async def publish(self, content, images):
        # 实现微博发布逻辑
        pass
```

### 3. 添加定时发布功能

```python
# workflow.py

import schedule
import time

def scheduled_publish(topic):
    # 执行发布逻辑
    pass

# 每天10点发布
schedule.every().day.at("10:00").do(scheduled_publish, "每日分享")

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 4. 添加内容审核

```python
# 新建 modules/content_filter.py

class ContentFilter:
    def __init__(self):
        self.blocked_words = ["敏感词1", "敏感词2"]
    
    def check(self, content: str) -> bool:
        for word in self.blocked_words:
            if word in content:
                return False
        return True
```

### 5. 添加数据统计

```python
# 新建 modules/analytics.py

import json
from datetime import datetime

class Analytics:
    def __init__(self, log_file="publish_log.json"):
        self.log_file = log_file
    
    def log_publish(self, topic, title, success):
        record = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "title": title,
            "success": success
        }
        # 追加到日志文件
        with open(self.log_file, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

## 常见问题排查

### 1. 选择器失效

小红书页面更新后，元素选择器可能失效。排查步骤：

```python
# 在 xhs_playwright.py 中添加调试
await self.page.screenshot(path="debug.png")
print(await self.page.content())
```

使用浏览器开发者工具检查新的选择器。

### 2. API调用失败

```python
# 添加详细错误日志
try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"HTTP错误: {e}")
    print(f"响应内容: {e.response.text}")
```

### 3. 登录状态丢失

删除浏览器数据重新登录：
```bash
rm -rf ~/.xhs_browser_data
```

## 测试

```python
# 测试文案生成
python -c "
from modules.content_generator import ContentGenerator
g = ContentGenerator()
result = g.search_and_generate('测试主题')
print(result)
"

# 测试图片生成
python -c "
from modules.image_fetcher import ImageFetcher
f = ImageFetcher('images')
result = f.search_and_download(['测试'], count=1)
print(result)
"
```

## 环境变量完整列表

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `SILICONFLOW_API_KEY` | 是 | - | 硅基流动API密钥 |
| `SILICONFLOW_MODEL` | 否 | `Qwen/Qwen2.5-72B-Instruct` | 文案生成模型 |
| `SILICONFLOW_IMAGE_API_KEY` | 否 | 同上 | 图片生成API密钥 |
| `SILICONFLOW_IMAGE_MODEL` | 否 | `Kwai-Kolors/Kolors` | 图片生成模型 |

## 参考资源

- [硅基流动API文档](https://docs.siliconflow.cn)
- [Playwright Python文档](https://playwright.dev/python/)
- [小红书创作中心](https://creator.xiaohongshu.com)

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request
