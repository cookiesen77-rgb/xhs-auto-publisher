"""图片获取模块 - 使用硅基流动AI生成图片"""
import os
import requests
import hashlib
import random
from pathlib import Path
from typing import List
from urllib.parse import quote

class ImageFetcher:
    def __init__(self, output_dir: str = "../images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        # 图片生成使用单独的API key（如果有），否则使用通用key
        self.api_key = os.getenv('SILICONFLOW_IMAGE_API_KEY') or os.getenv('SILICONFLOW_API_KEY')
        self.api_url = "https://api.siliconflow.cn/v1/images/generations"
        # 文生图模型
        self.model = os.getenv('SILICONFLOW_IMAGE_MODEL', 'Kwai-Kolors/Kolors')

    def search_and_download(self, keywords: List[str], count: int = 3) -> List[str]:
        """根据关键词生成图片"""
        downloaded_images = []

        for i, keyword in enumerate(keywords[:count]):
            # 优先使用AI生成图片
            image_path = self._generate_with_ai(keyword, i)
            # 备用方案
            if not image_path:
                image_path = self._download_from_picsum(i)
            if image_path:
                downloaded_images.append(image_path)

        return downloaded_images

    def _generate_with_ai(self, keyword: str, index: int = 0) -> str:
        """使用硅基流动AI生成图片"""
        if not self.api_key:
            print("⚠️  未配置 SILICONFLOW_API_KEY，跳过AI生图")
            return None

        try:
            # 构建更详细的prompt
            prompt = self._enhance_prompt(keyword)
            print(f"🎨 AI生成图片: {keyword}")

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "prompt": prompt,
                "seed": random.randint(0, 9999999999)
            }

            # Qwen-Image-Edit 模型需要参考图片
            if "Qwen-Image-Edit" in self.model or "Qwen/Qwen-Image" in self.model:
                # 获取一张随机图片作为参考基础
                ref_image_url = self._get_reference_image()
                payload["image"] = ref_image_url
                payload["cfg"] = 4.0
                payload["num_inference_steps"] = 50
            else:
                # Kolors 等纯文生图模型
                payload["image_size"] = "1024x1024"
                payload["num_inference_steps"] = 20
                payload["guidance_scale"] = 7.5

            response = requests.post(self.api_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            if result.get('images') and len(result['images']) > 0:
                image_url = result['images'][0]['url']
                return self._download_image(image_url, f"ai_{index}_{hashlib.md5(keyword.encode()).hexdigest()[:8]}.jpg")

        except requests.exceptions.HTTPError as e:
            print(f"⚠️  AI生图API错误: {e}")
            # 打印详细错误
            try:
                print(f"   详情: {e.response.text}")
            except:
                pass
        except Exception as e:
            print(f"⚠️  AI生图失败: {e}")
        return None

    def _enhance_prompt(self, keyword: str) -> str:
        """增强prompt以获得更好的图片效果"""
        # 添加通用的图片质量描述
        quality_suffix = ", high quality, detailed, professional photography, good lighting, 4k"
        
        # 针对中文关键词，添加一些风格描述
        if any('\u4e00' <= char <= '\u9fff' for char in keyword):
            # 包含中文，添加中英混合描述
            enhanced = f"{keyword}, beautiful scene, aesthetic composition{quality_suffix}"
        else:
            enhanced = f"{keyword}{quality_suffix}"
        
        return enhanced

    def _get_reference_image(self) -> str:
        """获取参考图片URL（用于Qwen-Image-Edit模型）"""
        # 使用 picsum 随机图片作为参考
        seed = random.randint(1, 1000)
        return f"https://picsum.photos/seed/{seed}/512/512"

    def _download_image(self, url: str, filename: str) -> str:
        """从URL下载图片"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"✅ 已生成图片: {filepath}")
                return filepath
        except Exception as e:
            print(f"下载图片失败: {e}")
        return None

    def _download_from_picsum(self, seed: int = None) -> str:
        """从 Lorem Picsum 下载随机图片（备用方案）"""
        try:
            seed = seed or random.randint(1, 1000)
            url = f"https://picsum.photos/seed/{seed}/800/600"
            response = requests.get(url, timeout=15, allow_redirects=True)
            if response.status_code == 200 and len(response.content) > 1000:
                filename = f"picsum_{seed}.jpg"
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"已下载图片(Picsum备用)：seed={seed} -> {filepath}")
                return filepath
        except Exception as e:
            print(f"下载图片失败(Picsum): {e}")
        return None

    def download_from_url(self, url: str, filename: str = None) -> str:
        """从指定URL下载图片"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                if not filename:
                    filename = hashlib.md5(url.encode()).hexdigest() + ".jpg"

                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)

                print(f"已下载图片：{filepath}")
                return filepath
        except Exception as e:
            print(f"下载图片失败 {url}: {e}")

        return None


if __name__ == "__main__":
    fetcher = ImageFetcher()
    keywords = ["nature", "travel", "food"]
    images = fetcher.search_and_download(keywords)
    print(f"下载完成，共 {len(images)} 张图片：")
    for img in images:
        print(f"  - {img}")
