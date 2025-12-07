"""小红书自动发布模块 - 使用Playwright自动化"""
import json
import os
import time
import asyncio
from pathlib import Path
from typing import List, Dict, Optional


class XHSPublisher:
    """使用Playwright自动发布到小红书"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.user_data_dir = Path.home() / ".xhs_browser_data"

    async def init_browser(self):
        """初始化浏览器"""
        from playwright.async_api import async_playwright

        self.playwright = await async_playwright().start()

        # 使用持久化上下文保存登录状态
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=self.headless,
            viewport={"width": 1280, "height": 800},
            locale="zh-CN"
        )

        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()

    async def close(self):
        """关闭浏览器"""
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

    async def check_login(self) -> bool:
        """检查是否已登录"""
        await self.page.goto("https://creator.xiaohongshu.com/publish/publish")
        await self.page.wait_for_load_state("networkidle")

        # 检查是否需要登录
        if "login" in self.page.url.lower():
            return False

        # 检查是否在发布页面
        try:
            await self.page.wait_for_selector('input[type="file"]', timeout=5000)
            return True
        except:
            return False

    async def wait_for_login(self, timeout: int = 120):
        """等待用户手动登录"""
        print("\n⚠️  请在浏览器中完成登录...")
        print(f"⏰ 等待登录，超时时间: {timeout}秒\n")

        await self.page.goto("https://creator.xiaohongshu.com/login")

        start_time = time.time()
        while time.time() - start_time < timeout:
            await asyncio.sleep(2)

            # 检查是否已登录成功
            if "login" not in self.page.url.lower():
                print("✅ 登录成功！")
                return True

        print("❌ 登录超时")
        return False

    async def publish(self, title: str, content: str, images: List[str], tags: List[str] = None) -> Dict:
        """
        发布笔记到小红书

        Args:
            title: 笔记标题
            content: 笔记正文
            images: 图片路径列表
            tags: 话题标签列表

        Returns:
            发布结果
        """
        result = {"success": False, "message": ""}

        try:
            # 进入发布页面
            await self.page.goto("https://creator.xiaohongshu.com/publish/publish")
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # 检查登录状态
            if "login" in self.page.url.lower():
                logged_in = await self.wait_for_login()
                if not logged_in:
                    result["message"] = "登录失败或超时"
                    return result

                # 重新进入发布页面
                await self.page.goto("https://creator.xiaohongshu.com/publish/publish")
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)

            print(f"📍 当前页面: {self.page.url}")

            # 切换到"上传图文"标签（默认可能是视频）
            try:
                await self.page.evaluate('''() => {
                    const tabs = document.querySelectorAll('div');
                    for (let tab of tabs) {
                        if (tab.textContent === '上传图文' && tab.textContent.length < 10) {
                            tab.click();
                            return true;
                        }
                    }
                    return false;
                }''')
                await asyncio.sleep(2)
            except:
                pass

            # 上传图片
            if images:
                print(f"📷 上传 {len(images)} 张图片...")
                try:
                    file_input = await self.page.wait_for_selector('input[type="file"]', timeout=10000)
                    abs_images = [str(Path(img).resolve()) for img in images if Path(img).exists()]
                    if abs_images:
                        await file_input.set_input_files(abs_images)
                        print(f"✅ 已选择 {len(abs_images)} 张图片")
                        # 等待图片上传和页面切换到编辑界面
                        await asyncio.sleep(5)
                except Exception as e:
                    print(f"⚠️  图片上传跳过: {e}")
            else:
                # 无图片时需要先上传一张占位图才能进入编辑界面
                print("⚠️  没有图片，小红书图文笔记需要至少一张图片")
                result["message"] = "小红书图文笔记需要至少一张图片"
                return result

            # 等待编辑界面加载
            await asyncio.sleep(3)

            # 填写标题 - 使用小红书实际的选择器
            print("📝 填写标题...")
            try:
                title_input = await self.page.wait_for_selector(
                    'input[placeholder*="标题"], input.d-text',
                    timeout=10000
                )
                if title_input:
                    await title_input.click()
                    await title_input.fill(title)
                    print(f"✅ 标题已填写: {title[:20]}...")
            except Exception as e:
                print(f"⚠️  标题填写失败: {e}")

            # 填写正文 - 使用 ProseMirror 富文本编辑器
            print("📝 填写正文...")
            full_content = content
            if tags:
                tag_str = " ".join([f"#{tag}" for tag in tags])
                full_content = f"{content}\n\n{tag_str}"

            try:
                # 小红书使用 tiptap/ProseMirror 编辑器，需要用 JS 直接设置内容
                # 将换行转换为 <p> 标签
                paragraphs = full_content.split('\n')
                html_content = ''.join([f'<p>{p}</p>' if p.strip() else '<p></p>' for p in paragraphs])
                
                await self.page.evaluate(f'''() => {{
                    const editor = document.querySelector('.tiptap.ProseMirror, div[contenteditable="true"]');
                    if (editor) {{
                        editor.innerHTML = `{html_content}`;
                        editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        return true;
                    }}
                    return false;
                }}''')
                print(f"✅ 正文已填写 ({len(full_content)} 字)")
            except Exception as e:
                print(f"⚠️  正文填写失败: {e}")
                # 备用方案：点击并输入
                try:
                    content_input = await self.page.wait_for_selector(
                        '.tiptap.ProseMirror, div[contenteditable="true"]',
                        timeout=5000
                    )
                    if content_input:
                        await content_input.click()
                        await self.page.keyboard.type(full_content, delay=5)
                        print(f"✅ 正文已填写（键盘输入）")
                except:
                    pass

            await asyncio.sleep(2)

            # 点击发布按钮
            print("🚀 准备发布...")
            try:
                # 小红书发布按钮的精确选择器
                publish_btn = await self.page.wait_for_selector(
                    'button.publishBtn, button:has-text("发布")',
                    timeout=10000
                )
                if publish_btn:
                    is_enabled = await publish_btn.is_enabled()
                    if is_enabled:
                        await publish_btn.click()
                        print("✅ 已点击发布按钮")
                        await asyncio.sleep(5)
                        result["success"] = True
                        result["message"] = "发布操作已执行，请检查是否成功"
                    else:
                        result["message"] = "发布按钮不可点击，可能内容不完整"
                        print("⚠️  发布按钮不可点击")
            except Exception as e:
                result["message"] = f"点击发布按钮失败: {e}"
                print(f"⚠️  点击发布按钮失败: {e}")

            if result["success"]:
                print("✅ 发布操作完成！")
            else:
                # 保存截图以便调试
                screenshot_path = str(Path(__file__).parent.parent / "output" / "debug_screenshot.png")
                await self.page.screenshot(path=screenshot_path)
                print(f"📸 已保存截图: {screenshot_path}")

        except Exception as e:
            result["message"] = f"发布失败: {str(e)}"
            print(f"❌ 发布失败: {e}")
            try:
                screenshot_path = str(Path(__file__).parent.parent / "output" / "error_screenshot.png")
                await self.page.screenshot(path=screenshot_path)
                print(f"📸 已保存错误截图: {screenshot_path}")
            except:
                pass

        return result


async def publish_note(draft_path: str, image_folder: str, headless: bool = False) -> Dict:
    """
    发布笔记的便捷函数

    Args:
        draft_path: 草稿JSON文件路径
        image_folder: 图片文件夹路径
        headless: 是否无头模式

    Returns:
        发布结果
    """
    # 加载草稿
    with open(draft_path, 'r', encoding='utf-8') as f:
        draft = json.load(f)

    title = draft.get("title", "")
    content = draft.get("content", "")
    tags = draft.get("tags", [])

    # 获取图片列表
    images = []
    img_dir = Path(image_folder)
    if img_dir.exists():
        images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png"))
        images = [str(p) for p in images]

    print(f"\n📋 发布内容预览:")
    print(f"标题: {title}")
    print(f"正文: {content[:100]}...")
    print(f"标签: {', '.join(tags)}")
    print(f"图片: {len(images)} 张\n")

    # 初始化发布器
    publisher = XHSPublisher(headless=headless)

    try:
        await publisher.init_browser()
        result = await publisher.publish(title, content, images, tags)
    finally:
        await publisher.close()

    return result


def run_publish(draft_path: str, image_folder: str, headless: bool = False) -> Dict:
    """同步版本的发布函数"""
    return asyncio.run(publish_note(draft_path, image_folder, headless))


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python xhs_playwright.py <draft_json> <image_folder>")
        print("示例: python xhs_playwright.py ../output/draft_xxx.json ../images")
        sys.exit(1)

    draft_path = sys.argv[1]
    image_folder = sys.argv[2]

    if not Path(draft_path).exists():
        print(f"❌ 草稿文件不存在: {draft_path}")
        sys.exit(1)

    result = run_publish(draft_path, image_folder)
    print(f"\n发布结果: {result}")
