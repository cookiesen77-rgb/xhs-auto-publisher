"""内容生成模块 - 使用硅基流动API生成文案"""
import json
import os
import requests
from datetime import datetime

class ContentGenerator:
    def __init__(self):
        self.api_key = os.getenv('SILICONFLOW_API_KEY')
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model = os.getenv('SILICONFLOW_MODEL', 'Qwen/Qwen2.5-72B-Instruct')

    def search_and_generate(self, topic: str) -> dict:
        """基于主题生成文案"""
        prompt = f"""基于以下主题生成小红书风格的文案：

主题：{topic}

请生成：
1. 吸引人的标题（带emoji，20字以内）
2. 正文内容（200-500字，分段，带emoji）
3. 5-10个相关话题标签
4. 3-5个建议的图片关键词

返回JSON格式：
{{
    "title": "标题",
    "content": "正文",
    "tags": ["标签1", "标签2"],
    "image_keywords": ["关键词1", "关键词2"]
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
            "temperature": 0.7
        }

        # DeepSeek-R1 是推理模型，需要更长的超时时间
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=180)
        response.raise_for_status()

        result = response.json()
        content_text = result['choices'][0]['message']['content']
        
        # DeepSeek-R1 可能返回 reasoning_content，我们只需要最终答案
        if 'reasoning_content' in result['choices'][0]['message']:
            print("  (推理完成，提取最终答案...)")

        try:
            start_idx = content_text.find('{')
            end_idx = content_text.rfind('}') + 1
            json_str = content_text[start_idx:end_idx]
            result = json.loads(json_str)
        except:
            result = {
                "title": topic,
                "content": content_text,
                "tags": [],
                "image_keywords": [topic]
            }

        result['created_at'] = datetime.now().isoformat()
        result['original_topic'] = topic

        return result

    def save_draft(self, content: dict, output_path: str):
        """保存草稿到JSON文件"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        print(f"草稿已保存到：{output_path}")


if __name__ == "__main__":
    generator = ContentGenerator()

    topic = input("请输入主题想法：")
    result = generator.search_and_generate(topic)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    output_path = f"../output/draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    generator.save_draft(result, output_path)
