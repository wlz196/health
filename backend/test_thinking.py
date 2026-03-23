import sys
import os
sys.path.append("/Users/wanglianzuo/health/backend")
from dotenv import load_dotenv
load_dotenv()

from zhipuai import ZhipuAI

client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

try:
    response = client.chat.completions.create(
        model="glm-4.7-flash",
        messages=[{"role": "user", "content": "你好"}],
        thinking={"type": "disabled"}
    )
    print("✅ Success! Response:", response.choices[0].message.content)
except Exception as e:
    print("❌ Error:", str(e))
