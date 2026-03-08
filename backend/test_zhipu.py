from dotenv import load_dotenv
import os
load_dotenv()
from core.ai_nutritionist import identify_food_text
from zhipuai import ZhipuAI

api_key = os.getenv("ZHIPU_API_KEY")
client = ZhipuAI(api_key=api_key)
prompt = "一盘菜花炒肉"
response = client.chat.completions.create(
    model="glm-4",
    messages=[
        {"role": "user", "content": prompt}
    ]
)
print(response)
