import sys
import os
sys.path.append("/Users/wanglianzuo/health/backend")

# 加载 .env
from dotenv import load_dotenv
load_dotenv()

from core.ai_nutritionist import identify_food_text

def test_prompt(description):
    print(f"\n[测试文本]: {description}")
    try:
        result = identify_food_text(description)
        print("💡 AI 返回结果:", result)
        
        # 能量守恒验证
        if isinstance(result, dict) and "kcal" in result:
            p = result.get("protein", 0)
            f = result.get("fat", 0)
            c = result.get("carb", 0)
            calc_kcal = p * 4 + f * 9 + c * 4
            diff = abs(result["kcal"] - calc_kcal)
            print(f"📊 数学 formula 验算：({p}*4) + ({f}*9) + ({c}*4) = {calc_kcal} kcal")
            if diff < 5:
                print("✅ 能量守恒断言：通过")
            else:
                print("⚠️ 能量守恒断言：不相符")
    except Exception as e:
        print("❌ 解析错误:", str(e))

if __name__ == "__main__":
    test_prompt("炸鸡腿（不吃皮）")
    test_prompt("红烧肉（只吃瘦部分，而且在水里涮过了）")
    test_prompt("两片全麦面包，一个煎蛋（不加盐）")
    test_prompt("两个不带蛋黄的鸡蛋")
