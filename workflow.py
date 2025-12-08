#!/usr/bin/env python3
"""
小红书发布工作流 - 主程序
从想法到发布的完整自动化流程（独立运行，不依赖Claude）
"""

import sys
import os
import asyncio
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'modules'))

from content_generator import ContentGenerator
from image_fetcher import ImageFetcher
from xhs_playwright import XHSPublisher
import glob


def main():
    print("=" * 60)
    print("🎨 小红书智能发布工作流")
    print("=" * 60)
    print("📌 使用硅基流动API生成内容 + Playwright自动发布")
    print("=" * 60)

    topic = input("\n💡 请输入你的想法或主题: ").strip()

    if not topic:
        print("❌ 主题不能为空")
        return

    print(f"\n✅ 收到主题: {topic}\n")

    # 步骤1: 生成文案
    print("📝 步骤1: 生成文案...")
    generator = ContentGenerator()
    content = generator.search_and_generate(topic)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    draft_filename = f"draft_{timestamp}.json"
    draft_path = Path(__file__).parent / "output" / draft_filename

    generator.save_draft(content, str(draft_path))

    print(f"\n📄 文案预览:")
    print(f"标题: {content['title']}")
    print(f"正文: {content['content'][:100]}...")
    print(f"标签: {', '.join(content['tags'])}")

    # 步骤2: 下载图片
    print(f"\n🖼️  步骤2: 下载相关图片...")
    image_keywords = content.get('image_keywords', [topic])
    image_dir = Path(__file__).parent / "images"
    fetcher = ImageFetcher(str(image_dir))
    images = fetcher.search_and_download(image_keywords, count=3)

    if not images:
        print("⚠️  未能下载图片，将继续发布流程（无图片）")
    else:
        print(f"\n✅ 已下载 {len(images)} 张图片")

    # 步骤3: 询问是否自动发布
    print(f"\n" + "=" * 60)
    print("🚀 步骤3: 发布到小红书")
    print("=" * 60)

    print("\n请选择发布方式:")
    print("  1. 自动发布（使用Playwright自动化）")
    print("  2. 仅生成内容（手动复制发布）")

    choice = input("\n请输入选项 [1/2]: ").strip()

    if choice == "1":
        # 自动发布
        print("\n🚀 启动自动发布...")
        asyncio.run(auto_publish(content, images))
        
        # 清理本地生成的文件
        cleanup_local_files(str(draft_path), images)
    else:
        # 仅生成内容
        print(f"\n📁 草稿文件已保存: {draft_path}")
        print(f"📁 图片文件夹: {image_dir}")
        print("\n💡 请手动复制内容到小红书创作中心发布:")
        print(f"   https://creator.xiaohongshu.com/publish/publish")

    print(f"\n" + "=" * 60)
    print("✨ 工作流完成!")
    print("=" * 60)


def cleanup_local_files(draft_path: str, images: list):
    """清理本地生成的文件"""
    print("\n🧹 清理本地文件...")
    
    # 删除草稿文件
    try:
        if os.path.exists(draft_path):
            os.remove(draft_path)
            print(f"  已删除草稿: {draft_path}")
    except Exception as e:
        print(f"  ⚠️ 删除草稿失败: {e}")
    
    # 删除图片文件
    for img_path in images:
        try:
            if os.path.exists(img_path):
                os.remove(img_path)
                print(f"  已删除图片: {img_path}")
        except Exception as e:
            print(f"  ⚠️ 删除图片失败: {e}")
    
    print("✅ 本地文件清理完成")


async def auto_publish(content: dict, images: list):
    """自动发布到小红书"""
    publisher = XHSPublisher(headless=False)

    try:
        print("🌐 启动浏览器...")
        await publisher.init_browser()

        # 检查登录状态
        logged_in = await publisher.check_login()
        if not logged_in:
            print("\n⚠️  需要登录小红书账号")
            logged_in = await publisher.wait_for_login(timeout=120)
            if not logged_in:
                print("❌ 登录超时，请重试")
                return

        # 发布笔记
        result = await publisher.publish(
            title=content['title'],
            content=content['content'],
            images=images,
            tags=content.get('tags', [])
        )

        if result['success']:
            print("\n🎉 笔记发布成功！")
        else:
            print(f"\n⚠️  {result['message']}")

    finally:
        await publisher.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  工作流已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
