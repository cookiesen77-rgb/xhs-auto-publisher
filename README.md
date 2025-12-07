# 小红书自动发布工作流

一个从想法到发布的完整自动化工作流系统，使用 AI 生成内容和图片，通过 Playwright 自动发布到小红书。

## 功能特性

- **AI 文案生成** - 使用硅基流动 API（DeepSeek-R1）自动生成小红书风格文案
- **AI 图片生成** - 使用硅基流动 API（Kolors）根据关键词生成配图
- **自动化发布** - 使用 Playwright 自动登录、上传图片、填写内容并发布
- **完全独立** - 不依赖 Claude 或其他 MCP 工具，可独立运行

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/xhs-auto-publisher.git
cd xhs-auto-publisher
```

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 3. 配置 API 密钥

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API 密钥
```

获取 API 密钥：https://cloud.siliconflow.cn

### 4. 运行

```bash
python workflow.py
```

## 配置说明

在 `.env` 文件中配置：

```bash
# 硅基流动 API 密钥（必填）
SILICONFLOW_API_KEY=your-api-key

# 文案生成模型（可选，默认 Qwen/Qwen2.5-72B-Instruct）
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-R1

# 图片生成 API 密钥（可选，默认使用上面的 key）
SILICONFLOW_IMAGE_API_KEY=your-image-api-key

# 图片生成模型（可选，默认 Kwai-Kolors/Kolors）
SILICONFLOW_IMAGE_MODEL=Kwai-Kolors/Kolors
```

## 使用方法

### 方式 1：完整工作流（推荐）

```bash
python workflow.py
```

按提示操作：
1. 输入主题想法（如"冬日咖啡推荐"）
2. AI 自动生成文案和图片
3. 选择发布方式：自动发布或手动复制

### 方式 2：使用启动菜单

```bash
./start.sh
```

### 方式 3：分步执行

```bash
# 仅生成文案
cd modules && python content_generator.py

# 仅生成图片
python image_fetcher.py

# 仅发布（需要已有草稿）
python xhs_playwright.py ../output/draft_xxx.json ../images/
```

## 项目结构

```
xhs-auto-publisher/
├── workflow.py              # 主工作流入口
├── start.sh                 # 快速启动脚本
├── modules/
│   ├── content_generator.py # AI 文案生成
│   ├── image_fetcher.py     # AI 图片生成
│   └── xhs_playwright.py    # Playwright 自动发布
├── output/                  # 生成的草稿文件
├── images/                  # 生成的图片文件
├── .env.example             # 环境变量模板
├── requirements.txt         # Python 依赖
└── README.md               # 说明文档
```

## 支持的模型

### 文案生成模型
- `deepseek-ai/DeepSeek-R1` - 推理能力强，生成质量高
- `Qwen/Qwen2.5-72B-Instruct` - 通用模型
- `Qwen/QwQ-32B` - 轻量级推理模型

### 图片生成模型
- `Kwai-Kolors/Kolors` - 纯文生图，效果好
- `Qwen/Qwen-Image` - 通用图片生成

## 注意事项

1. **首次使用**需要在浏览器中手动登录小红书账号，登录状态会保存
2. **图片要求**：小红书图文笔记至少需要一张图片
3. **发布限制**：请遵守小红书平台规则，避免频繁发布
4. **API 费用**：硅基流动 API 按量计费，请关注使用量

## 常见问题

**Q: 登录状态如何保存？**

A: Playwright 使用持久化上下文，登录状态保存在 `~/.xhs_browser_data` 目录

**Q: 图片生成失败怎么办？**

A: 会自动使用 Picsum 备用图片源，确保流程不中断

**Q: 如何更换模型？**

A: 修改 `.env` 文件中的 `SILICONFLOW_MODEL` 或 `SILICONFLOW_IMAGE_MODEL`

## License

MIT License
