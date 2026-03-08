from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from database import engine, Base
from core.garmin_client import init_garmin_client
from core.ai_nutritionist import identify_food
from datetime import date
import os
import base64
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载环境变量 (包括 GEMINI_API_KEY)
load_dotenv()

# 初始化数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Health Dashboard")

# 启用 GZip 响应压缩，减少传输带宽（默认压>500字节的数据）
app.add_middleware(GZipMiddleware, minimum_size=500)

# 解决跨域问题，允许 Vue 本地发来的请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_garmin():
    """获取一个初始化好的 Garmin 客户端（依赖于您刚生成的 Token）"""
    token_dir = os.path.expanduser("~/.garminconnect")
    try:
        # 只传 token_dir，让底层自动尝试拉取凭证
        return init_garmin_client(token_dir=token_dir)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Garmin 未授权或 Token 失效: {e}")

@app.get("/api/overview")
def get_daily_overview():
    """获取今日总览（卡路里、步数等）及昨日睡眠"""
    garmin = get_garmin()
    today = date.today().isoformat()
    
    try:
        summary = garmin.get_user_summary(today)
        sleep_data = garmin.get_sleep_data(today)
        
        # 提取睡眠核心信息 (如果有数据)
        sleep_duration_hrs = 0
        sleep_score = 0
        sleep_stage_deep = 0
        sleep_stage_light = 0
        
        if sleep_data and "dailySleepDTO" in sleep_data:
            dto = sleep_data["dailySleepDTO"]
            # 单位为秒
            sleep_duration_seconds = dto.get("sleepTimeSeconds", 0)
            sleep_duration_hrs = round(sleep_duration_seconds / 3600, 1)
            sleep_score = dto.get("sleepScores", {}).get("overall", {}).get("value", 0)
            sleep_stage_deep = round(dto.get("deepSleepSeconds", 0) / 60) # 分钟
            sleep_stage_light = round(dto.get("lightSleepSeconds", 0) / 60) # 分钟

        return {
            "date": today,
            "totalSteps": summary.get("totalSteps", 0),
            "stepGoal": summary.get("dailyStepGoal", 0),
            "activeKilocalories": summary.get("activeKilocalories", 0),
            "bmrKilocalories": summary.get("bmrKilocalories", 0),
            "consumedKilocalories": summary.get("consumedKilocalories", 0), # 摄入
            "sleepHrs": sleep_duration_hrs,
            "sleepScore": sleep_score,
            "deepSleepMins": sleep_stage_deep,
            "lightSleepMins": sleep_stage_light
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/activities")
def get_recent_activities():
    """获取最近的运动记录（有氧/无氧）"""
    garmin = get_garmin()
    try:
        # 获取最近 10 条活动
        activities = garmin.get_activities(0, 10)
        
        parsed = []
        for act in activities:
            parsed.append({
                "id": act.get("activityId"),
                "name": act.get("activityName"),
                "type": act.get("activityType", {}).get("typeKey"), # e.g., running, cycling、strength_training
                "durationMinutes": round(act.get("duration", 0) / 60, 1),
                "distanceKm": round(act.get("distance", 0) / 1000, 2),
                "calories": act.get("calories"),
                "startTimeLocal": act.get("startTimeLocal")
            })
        return parsed
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Placeholder for AI Food Recognition Request Body
class FoodImageRequest(BaseModel):
    image_base64: str

@app.post("/api/intake/identify")
def identify_food_endpoint(req: FoodImageRequest):
    """AI 食物识别"""
    # Vue 会传类似 "data:image/jpeg;base64,/9j/4AAQSk..." 的内容，我们需要裁掉前缀
    base64_data = req.image_base64
    if "base64," in base64_data:
        base64_data = base64_data.split("base64,")[1]
    
    try:
        # 直接透传清理掉前缀的 base64 字符串给 ZhipuAI
        from core.ai_nutritionist import identify_food
        result = identify_food(base64_data)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # 为了配合现有业务闭环，在这里您可以顺手写进 SQLite 里的 food_logs
        # 但是作为 MVP 我们可以先直接返回让前端渲染确认
        return result
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"解析或识别时发生错误: {str(e)}")

class FoodTextRequest(BaseModel):
    description: str

@app.post("/api/intake/identify_text")
def identify_food_text_endpoint(req: FoodTextRequest):
    """AI 文本食物识别"""
    try:
        from core.ai_nutritionist import identify_food_text
        result = identify_food_text(req.description)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"解析或识别时发生错误: {str(e)}")
