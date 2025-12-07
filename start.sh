#!/bin/bash

# 小红书发布工作流启动脚本（独立运行版）

echo "🎨 小红书智能发布工作流"
echo "======================="
echo "📌 使用硅基流动API + Playwright"
echo ""

# 检查环境变量
if [ -z "$SILICONFLOW_API_KEY" ]; then
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
fi

if [ -z "$SILICONFLOW_API_KEY" ]; then
    echo "⚠️  请先设置 SILICONFLOW_API_KEY 环境变量"
    echo "   方式1: export SILICONFLOW_API_KEY=your-key"
    echo "   方式2: 创建 .env 文件并填入密钥"
    exit 1
fi

echo "选择操作:"
echo "1. 完整工作流（生成+发布）"
echo "2. 仅生成文案"
echo "3. 仅下载图片"
echo "4. 仅发布（使用已有草稿）"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo "启动完整工作流..."
        python workflow.py
        ;;
    2)
        echo "启动文案生成..."
        cd modules && python content_generator.py
        ;;
    3)
        echo "启动图片下载..."
        cd modules && python image_fetcher.py
        ;;
    4)
        read -p "请输入草稿文件路径: " draft
        echo "启动Playwright发布..."
        cd modules && python xhs_playwright.py "$draft" ../images/
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac
