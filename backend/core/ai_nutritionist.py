import os
import json
from zhipuai import ZhipuAI

def get_zhipu_client():
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        return None
    return ZhipuAI(api_key=api_key)

def identify_food(image_base64_str: str):
    """
    调用 智谱清言 (GLM-4V) 分析食物的卡路里和微量元素。
    """
    client = get_zhipu_client()
    if not client:
        return {"error": "未配置 ZHIPU_API_KEY，请检查后端 .env 文件"}
        
    prompt = '''
    作为营养专家，请识别图中的食物。输出 JSON 格式：
    {"name": "简化的食物名称", "kcal": 0, "protein": 0, "fat": 0, "carb": 0}。
    其中，所有的营养数值均为预估的总数值（比如这盘菜总共有多少卡路里）。
    若有多个食物请汇总。只输出 JSON。
    '''
    
    try:
        response = client.chat.completions.create(
            model="glm-4v-flash",  
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_base64_str
                            }
                        }
                    ]
                }
            ]
        )
        
        raw_text = response.choices[0].message.content.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        return json.loads(raw_text)
    except Exception as e:
        return {"error": f"AI 识别失败: {str(e)}"}

def identify_food_text(description: str):
    """
    调用 智谱清言 (GLM-4) 根据纯文本描述分析食物的卡路里和微量元素。
    """
    client = get_zhipu_client()
    if not client:
        return {"error": "未配置 ZHIPU_API_KEY，请检查后端 .env 文件"}
        
    prompt = f'''
    作为营养专家，请评估用户提供的食物描述：“{description}”。输出 JSON 格式：
    {{"name": "简化的食物名称", "kcal": 0, "protein": 0, "fat": 0, "carb": 0}}。
    其中，所有的营养数值均为预估的总数值（比如这盘菜总共有多少卡路里）。
    若有多个食物请汇总计算。只输出 JSON。
    '''
    
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        raw_text = response.choices[0].message.content.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
            
        return json.loads(raw_text)
    except Exception as e:
        return {"error": f"AI 文本解析失败: {str(e)}"}
