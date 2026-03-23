import os
import json
from zhipuai import ZhipuAI

def get_zhipu_client():
    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        return None
    return ZhipuAI(api_key=api_key)

def get_gemini_client():
    """初始化 Google Gemini 客户端"""
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    return genai

def identify_food(image_base64_str: str):
    """
    分析食物的卡路里和微量元素。（优先 Gemini 2.0 Flash，次选 智谱 GLM-4V）
    """
    gemini = get_gemini_client()
    zhipu = get_zhipu_client()

    prompt = '''
    作为营养专家，请识别图中的食物。
    
    计算规则：
    1. 【成分剥离】：识别图中的修饰条件（如去皮、少油、瘦肉等），合理扣除对应营养素。
    2. 【绝对禁止记为0】：除非是水等0卡物质，任何带有质量的食物单项或总体数值绝对不能输出为 0。
    3. 【能量守恒】：总热量(kcal)必须满足公式：kcal = (protein * 4) + (fat * 9) + (carb * 4)。
    4. 【汇总合并】：包含多个食物请合并计算总体。
    
    输出 JSON 格式：
    {"name": "简化的食物名称组合", "kcal": 0, "protein": 0, "fat": 0, "carb": 0}
    
    注意：其中所有的营养数值均为总数值。只输出 JSON 代码，内容严禁包含任何中文解释或标记符。
    '''

    if gemini:
        try:
            model = gemini.GenerativeModel("gemini-1.5-flash")
            pass 
        except: pass

    if not zhipu:
        return {"error": "未配置 ZHIPU_API_KEY，请检查后端 .env 文件"}

    try:
        response = zhipu.chat.completions.create(
            model="glm-4.6v-flash",  
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_base64_str}}
                    ]
                }
            ],
            thinking={"type": "disabled"}
        )
        raw_text = response.choices[0].message.content.strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:]
        if raw_text.endswith("```"): raw_text = raw_text[:-3]
        res_json = json.loads(raw_text)
        
        # 🌟 后端数学强制守恒
        p = res_json.get("protein", 0)
        f = res_json.get("fat", 0)
        c = res_json.get("carb", 0)
        res_json["kcal"] = round(p * 4 + f * 9 + c * 4)
        return res_json
        
    except Exception as e:
        return {"error": f"智谱 AI 识别失败: {str(e)}"}


def identify_food_text(description: str):
    """
    根据纯文本描述分析食物的卡路里和微量元素。（优先 Gemini 2.0 Flash，次选 智谱 GLM-4）
    """
    gemini = get_gemini_client()
    zhipu = get_zhipu_client()

    prompt = f'''
    作为营养专家，请评估用户提供的食物描述：“{description}”。
    
    计算规则：
    1. 【成分剥离】：精准识别并执行条件修饰词（如“不带”、“去皮”、“只吃瘦肉”、“去黄”等）。例：不带蛋黄意味着剔除全部脂肪，仅保留蛋清蛋白。
    2. 【绝对禁止记为0】：除非是纯水等0卡物质，带有重量的实物食物加工剥离后，宏量数值绝不能归0。
    3. 【能量守恒】：总热量(kcal)必须通过公式验算：kcal = (protein * 4) + (fat * 9) + (carb * 4)。
    4. 【汇总合并】：包含多个食物请合并计算总体营养素。
    
    【输出示例】：
    描述：“不带蛋黄的鸡蛋” -> {{"name": "蛋白", "kcal": 16, "protein": 4, "fat": 0, "carb": 0}}
    描述：“红烧肉（只吃瘦肉）” -> {{"name": "红烧肉(瘦肉)", "kcal": 143, "protein": 20, "fat": 7, "carb": 0}}
    
    输出 JSON 格式：
    {{"name": "简化的食物名称组合", "kcal": 0, "protein": 0, "fat": 0, "carb": 0}}
    
    注意：其中所有的营养数值均为总数值。只输出 JSON 代码，内容严禁包含任何中文解释或标记符。
    '''

    raw_text = ""
    # 🌟 1. 优先使用 Google Gemini 2.0 Flash
    if gemini:
        try:
            model = gemini.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
        except Exception as e:
            print(f"Gemini 调用失败，自动切换智谱: {str(e)}")

    # 🌟 2. 备选（或未配置时）使用智谱 GLM-4.7-Flash
    if not raw_text and zhipu:
        try:
            response = zhipu.chat.completions.create(
                model="glm-4.7-flash",
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"}
            )
            raw_text = response.choices[0].message.content.strip()
        except Exception as e:
            return {"error": f"所有 AI 识别服务均失败: {str(e)}"}

    if not raw_text:
        return {"error": "未连接到任何有效的 AI 服务，请检查 .env 配置"}

    try:
        if raw_text.startswith("```json"): raw_text = raw_text[7:]
        if raw_text.endswith("```"): raw_text = raw_text[:-3]
        res_json = json.loads(raw_text)
        
        p = res_json.get("protein", 0)
        f = res_json.get("fat", 0)
        c = res_json.get("carb", 0)
        res_json["kcal"] = round(p * 4 + f * 9 + c * 4)
        return res_json
    except Exception as e:
        return {"error": f"AI 文本解析失败，返回原始内容: {raw_text}"}
