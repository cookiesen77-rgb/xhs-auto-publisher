# 安装部署指南

本文档提供详细的安装和部署步骤。

## 系统要求

- Python 3.7+
- Chrome/Chromium 浏览器（Playwright 会自动安装）
- 网络连接（调用 API 和访问小红书）

## 详细安装步骤

### 1. 安装 Python

**macOS:**
```bash
# 使用 Homebrew
brew install python3

# 验证安装
python3 --version
```

**Windows:**
- 下载安装包：https://www.python.org/downloads/
- 安装时勾选 "Add Python to PATH"

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip
```

### 2. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/xhs-auto-publisher.git
cd xhs-auto-publisher
```

或者下载 ZIP 包解压。

### 3. 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 4. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

依赖列表：
- `requests` - HTTP 请求
- `python-dotenv` - 环境变量管理
- `playwright` - 浏览器自动化

### 5. 安装 Playwright 浏览器

```bash
# 安装 Chromium 浏览器
playwright install chromium

# 如果需要安装所有浏览器
# playwright install
```

### 6. 配置 API 密钥

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用其他编辑器
```

填入你的硅基流动 API 密钥：
```
SILICONFLOW_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 7. 验证安装

```bash
# 测试文案生成
python -c "
from modules.content_generator import ContentGenerator
print('文案生成模块 OK')
"

# 测试图片生成
python -c "
from modules.image_fetcher import ImageFetcher
print('图片生成模块 OK')
"

# 测试 Playwright
python -c "
from playwright.sync_api import sync_playwright
print('Playwright OK')
"
```

## 获取 API 密钥

1. 访问 https://cloud.siliconflow.cn
2. 注册/登录账号
3. 进入「API 密钥」页面
4. 创建新密钥并复制

## 首次运行

```bash
python workflow.py
```

首次运行时：
1. 会自动打开浏览器
2. 需要在浏览器中登录小红书账号
3. 登录成功后，状态会自动保存

## 常见安装问题

### Q: pip install 报错

```bash
# 升级 pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: playwright install 失败

```bash
# 手动下载浏览器
playwright install chromium --with-deps

# Linux 可能需要安装依赖
sudo apt install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1
```

### Q: 权限问题

```bash
# macOS/Linux 添加执行权限
chmod +x start.sh
```

### Q: 找不到模块

确保在正确的目录下运行：
```bash
cd xhs-auto-publisher
python workflow.py
```

## Docker 部署（可选）

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .

CMD ["python", "workflow.py"]
```

构建和运行：
```bash
docker build -t xhs-publisher .
docker run -it --rm -v $(pwd)/.env:/app/.env xhs-publisher
```

## 更新项目

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```
