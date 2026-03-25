from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import FoodLogs, SavedFood, UserConfig, WeightLog, AnaerobicLog, User
from core.garmin_client import init_garmin_client
from core.ai_nutritionist import identify_food
from datetime import date, datetime, timedelta, timezone
from typing import Optional
import os
import json
import base64
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载环境变量 (包括 GEMINI_API_KEY)
load_dotenv()

# 🌟 统一设置北京时间时区 (UTC+8)
CST = timezone(timedelta(hours=8))

def get_beijing_now():
    """获取当前北京时间"""
    return datetime.now(CST)

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

# === 🔓 用户安全与 JWT 鉴权体系 ===
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from core.auth import SECRET_KEY, ALGORITHM, verify_password, get_password_hash, create_access_token
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """获取当前登录用户 (Depends)"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="未授权或凭证失效，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- 注册登录控制器 ---
class UserAuth(BaseModel):
    username: str
    password: str

@app.post("/api/register")
def register(item: UserAuth, db: Session = Depends(get_db)):
    """账号注册"""
    existing = db.query(User).filter(User.username == item.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已已被注册")
    hashed = get_password_hash(item.password)
    new_user = User(username=item.username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "注册成功，快去登录吧"}

@app.post("/api/login")
def login(item: UserAuth, db: Session = Depends(get_db)):
    """账号登录"""
    user = db.query(User).filter(User.username == item.username).first()
    if not user or not verify_password(item.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(data={"sub": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "userId": user.id
    }

@app.get("/api/overview")
def get_daily_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取今日总览（卡路里、步数等）"""
    today = get_beijing_now().date().isoformat()
    
    # 累加本地饮食记录中的热量
    today_logs = db.query(FoodLogs).filter(FoodLogs.date == today, FoodLogs.user_id == current_user.id).all()
    local_consumed = sum(log.kcal for log in today_logs) if today_logs else 0
    
    # 结算宏量总量克数
    consumed_macros = {"carb": 0, "protein": 0, "fat": 0}
    if today_logs:
        for log in today_logs:
            try:
                import json
                m = json.loads(log.macros) if log.macros else {}
                consumed_macros["carb"] += m.get("carb", 0)
                consumed_macros["protein"] += m.get("protein", 0)
                consumed_macros["fat"] += m.get("fat", 0)
            except:
                pass
    
    # 读取本 BMR 配置
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    if not config:
        # 新用户自动初始化默认配置
        config = UserConfig(user_id=current_user.id)
        db.add(config)
        db.commit()
        db.refresh(config)
    
    def calculate_bmr(c):
        if not c or not all([getattr(c, f, None) for f in ['height', 'weight', 'age', 'gender']]):
            return c.bmr_kcal if c else 1500
        if c.gender == 'male':
            # Mifflin-St Jeor
            return 10 * c.weight + 6.25 * c.height - 5 * c.age + 5
        else:
            return 10 * c.weight + 6.25 * c.height - 5 * c.age - 161

    local_bmr = round(calculate_bmr(config))
    multiplier = config.activity_multiplier if config and config.activity_multiplier else 1.2
    tdee_kcal = round(local_bmr * multiplier)
    
    # 🌟 连胜系统 (Perfect Streak)
    from datetime import timedelta
    streak = 0
    check_date = get_beijing_now().date()
    
    while True:
        d_str = check_date.isoformat()
        d_logs = db.query(FoodLogs).filter(FoodLogs.date == d_str, FoodLogs.user_id == current_user.id).all()
        d_consumed = sum(l.kcal for l in d_logs) if d_logs else 0
        
        if not d_logs and check_date == get_beijing_now().date():
            # 今天还没吃饭打卡，不中断昨天的连胜
            check_date -= timedelta(days=1)
            continue
            
        if not d_logs:
            # 一旦没打卡直接断开
            break
            
        if d_consumed > tdee_kcal:
            # 爆表热量也断开连胜
            if check_date == get_beijing_now().date():
                streak = 0
            break
            
        streak += 1
        check_date -= timedelta(days=1)

    return {
        "date": today,
        "bmrKilocalories": local_bmr,
        "tdeeKilocalories": tdee_kcal,
        "consumedKilocalories": local_consumed,
        "consumedMacros": consumed_macros,
        "current_streak": streak
    }

@app.get("/api/overview/weekly_roast")
def get_weekly_roast(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取过去 7 天的饮食统计，交由智谱大模型生成毒舌/夸奖点评"""
    from datetime import timedelta
    import json
    end_date = get_beijing_now().date()
    start_date = end_date - timedelta(days=6)
    
    logs = db.query(FoodLogs).filter(
        FoodLogs.user_id == current_user.id,
        FoodLogs.date >= start_date.isoformat(),
        FoodLogs.date <= end_date.isoformat()
    ).all()
    
    # 按照日期分组宏量
    daily_stats = {}
    for i in range(7):
        d_str = (start_date + timedelta(days=i)).isoformat()
        daily_stats[d_str] = {"kcal": 0, "p": 0, "f": 0, "c": 0}
        
    for log in logs:
        if log.date in daily_stats:
            daily_stats[log.date]["kcal"] += log.kcal
            try:
                m = json.loads(log.macros) if log.macros else {}
                daily_stats[log.date]["p"] += m.get("protein", 0)
                daily_stats[log.date]["f"] += m.get("fat", 0)
                daily_stats[log.date]["c"] += m.get("carb", 0)
            except:
                pass
                
    # 构造成纯文本发给大模型
    report_lines = []
    for d, s in daily_stats.items():
        if s["kcal"] == 0:
            report_lines.append(f"{d}: 未打卡")
        else:
            report_lines.append(f"{d}: 摄入热量 {s['kcal']}kcal (蛋白{s['p']}g, 脂肪{s['f']}g, 碳水{s['c']}g)")
    
    weights = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id,
        WeightLog.date >= start_date.isoformat()
    ).order_by(WeightLog.date.asc()).all()
    
    w_line = "无体重记录变化"
    if weights and len(weights) > 1:
        w_line = f"体重变化: 从 {weights[0].weight}kg (在{weights[0].date}) 变为 {weights[-1].weight}kg (在{weights[-1].date})"
        
    final_report = "近7天饮食记录:\n" + "\n".join(report_lines) + "\n\n体重变化:\n" + w_line
    
    from core.ai_nutritionist import generate_weekly_roast
    roast_text = generate_weekly_roast(final_report)
    
    return {"roast": roast_text}


# endpoint /api/activities 已移除，前端已全面解耦 Garmin 活动流。

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

# --- Config Models and Endpoints ---
class UserConfigResponse(BaseModel):
    id: int
    target_kcal: int
    bmr_kcal: int
    height: Optional[float] = None
    weight: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    activity_multiplier: Optional[float] = 1.2

@app.get("/api/config", response_model=UserConfigResponse)
def get_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    if not config:
        config = UserConfig(user_id=current_user.id, target_kcal=2000, bmr_kcal=1500, activity_multiplier=1.2)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

class ConfigUpdateRequest(BaseModel):
    target_kcal: Optional[int] = None
    bmr_kcal: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    activity_multiplier: Optional[float] = None

@app.post("/api/config", response_model=UserConfigResponse)
def update_config(item: ConfigUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    if not config:
        config = UserConfig(user_id=current_user.id, target_kcal=2000, bmr_kcal=1500, activity_multiplier=1.2)
        db.add(config)
    
    if item.target_kcal is not None: config.target_kcal = item.target_kcal
    if item.bmr_kcal is not None: config.bmr_kcal = item.bmr_kcal
    if item.height is not None: config.height = item.height
    if item.weight is not None: config.weight = item.weight
    if item.age is not None: config.age = item.age
    if item.gender is not None: config.gender = item.gender
    if item.activity_multiplier is not None: config.activity_multiplier = item.activity_multiplier
        
    db.commit()
    db.refresh(config)
    return config

# --- Intake Models and Endpoints ---

class SavedFoodCreateAndResponse(BaseModel):
    name: str
    kcal: int
    protein: float = 0.0
    fat: float = 0.0
    carb: float = 0.0
    is_per_100g: bool = False

class SavedFoodItemResponse(SavedFoodCreateAndResponse):
    id: int

class FoodLogCreate(BaseModel):
    food_name: str
    kcal: int
    macros: dict
    time: Optional[str] = None  # HH:MM format

class FoodLogResponse(BaseModel):
    id: int
    date: str
    time: Optional[str]
    food_name: str
    kcal: int
    macros: dict
    img_path: Optional[str]

class RecommendRequest(BaseModel):
    kcal_left: float
    p_left: float
    f_left: float
    c_left: float

@app.post("/api/intake/recommend")
def recommend_meal_endpoint(req: RecommendRequest, current_user: User = Depends(get_current_user)):
    """依据实时缺口调用智谱模型反向推荐 3 组食谱"""
    from core.ai_nutritionist import recommend_meal
    res = recommend_meal(req.kcal_left, req.p_left, req.f_left, req.c_left)
    if not res:
        raise HTTPException(status_code=500, detail="AI 推餐失败")
    return res

@app.get("/api/intake/saved_foods", response_model=list[SavedFoodItemResponse])
def get_saved_foods(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取所有保存的快捷食物"""
    return db.query(SavedFood).filter(SavedFood.user_id == current_user.id).all()

@app.post("/api/intake/saved_foods", response_model=SavedFoodItemResponse)
def add_saved_food(item: SavedFoodCreateAndResponse, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """添加一个新的快捷食物"""
    new_food = SavedFood(
        name=item.name,
        kcal=item.kcal,
        protein=item.protein,
        fat=item.fat,
        carb=item.carb,
        is_per_100g=item.is_per_100g,
        user_id=current_user.id
    )
    db.add(new_food)
    db.commit()
    db.refresh(new_food)
    return new_food

@app.delete("/api/intake/saved_foods/{item_id}")
def delete_saved_food(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除指定的快捷食物"""
    food = db.query(SavedFood).filter(SavedFood.id == item_id, SavedFood.user_id == current_user.id).first()
    if not food:
        raise HTTPException(status_code=404, detail="未找到该食物")
    db.delete(food)
    db.commit()
    return {"status": "ok"}

@app.delete("/api/intake/logs/{log_id}")
def delete_food_log(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除单条饮食记录"""
    log = db.query(FoodLogs).filter(FoodLogs.id == log_id, FoodLogs.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="未找到该饮食记录")
    db.delete(log)
    db.commit()
    return {"status": "ok"}

@app.delete("/api/weight/{log_id}")
def delete_weight_log(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除单条体重记录"""
    log = db.query(WeightLog).filter(WeightLog.id == log_id, WeightLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="未找到该体重记录")
    db.delete(log)
    db.commit()
    return {"status": "ok"}

@app.delete("/api/anaerobic/{log_id}")
def delete_anaerobic_log(log_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除单条训练记录"""
    log = db.query(AnaerobicLog).filter(AnaerobicLog.id == log_id, AnaerobicLog.user_id == current_user.id).first()
    if not log:
        raise HTTPException(status_code=404, detail="未找到该训练记录")
    db.delete(log)
    db.commit()
    return {"status": "ok"}

@app.get("/api/intake/logs", response_model=list[FoodLogResponse])
def get_food_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取今日的饮食记录"""
    today = get_beijing_now().date().isoformat()
    logs = db.query(FoodLogs).filter(FoodLogs.date == today, FoodLogs.user_id == current_user.id).all()
    
    result = []
    for log in logs:
        try:
            macros = json.loads(log.macros) if log.macros else {}
        except:
            macros = {}
        result.append({
            "id": log.id,
            "date": log.date,
            "time": log.time,
            "food_name": log.food_name,
            "kcal": log.kcal,
            "macros": macros,
            "img_path": log.img_path
        })
    return result

@app.get("/api/intake/history")
def get_food_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取历史记录过的食物（按名字去重，最近 15 种）"""
    import json
    logs = db.query(FoodLogs).filter(FoodLogs.user_id == current_user.id).order_by(FoodLogs.date.desc(), FoodLogs.id.desc()).limit(50).all()
    # 内存去重
    seen = set()
    result = []
    for log in logs:
        if log.food_name not in seen:
            seen.add(log.food_name)
            try:
                macros = json.loads(log.macros) if log.macros else {}
            except:
                macros = {}
            result.append({
                "food_name": log.food_name,
                "kcal": log.kcal,
                "macros": macros
            })
    return result[:15]

@app.post("/api/intake/logs", response_model=FoodLogResponse)
def add_food_log(item: FoodLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """添加一条饮食记录"""
    now_cst = get_beijing_now()
    today = now_cst.date().isoformat()
    current_time = item.time or now_cst.strftime("%H:%M")
    
    new_log = FoodLogs(
        date=today,
        time=current_time,
        food_name=item.food_name,
        kcal=item.kcal,
        macros=json.dumps(item.macros),
        img_path=None,
        user_id=current_user.id
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    return {
        "id": new_log.id,
        "date": new_log.date,
        "time": new_log.time,
        "food_name": new_log.food_name,
        "kcal": new_log.kcal,
        "macros": json.loads(new_log.macros),
        "img_path": new_log.img_path
    }

# --- Weight Models and Endpoints ---
class WeightLogCreate(BaseModel):
    weight: float
    date: Optional[str] = None
    day_type: Optional[str] = None # 🌟 绑定今日运动模式

class WeightLogResponse(BaseModel):
    id: int
    date: str
    weight: float
    day_type: Optional[str] = None

@app.get("/api/weight", response_model=list[WeightLogResponse])
def get_weight_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取最近 10 次的体重记录 (日期升序利于画图)"""
    logs = db.query(WeightLog).filter(WeightLog.user_id == current_user.id).order_by(WeightLog.date.desc()).limit(10).all()
    # 颠倒为过去到现在的升序
    return list(reversed(logs))

@app.post("/api/weight", response_model=WeightLogResponse)
def add_weight_log(item: WeightLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """记录今日体重"""
    today = item.date or get_beijing_now().date().isoformat()
    existing = db.query(WeightLog).filter(WeightLog.date == today, WeightLog.user_id == current_user.id).first()
    
    saved_log = None
    if existing:
        existing.weight = item.weight
        if item.day_type:
            existing.day_type = item.day_type
        saved_log = existing
    else:
        new_log = WeightLog(date=today, weight=item.weight, day_type=item.day_type, user_id=current_user.id)
        db.add(new_log)
        saved_log = new_log
    
    # 🔥 反向更新个人配置 (体重并重算 BMR)
    config = db.query(UserConfig).filter(UserConfig.user_id == current_user.id).first()
    if config:
        config.weight = item.weight
        # Mifflin-St Jeor formula calculation
        if config.height and config.age and config.gender:
            base_bmr = 10 * config.weight + 6.25 * config.height - 5 * config.age
            config.bmr_kcal = int(base_bmr + 5) if config.gender == "male" else int(base_bmr - 161)
            
    db.commit()
    db.refresh(saved_log)
    return saved_log

# === 无氧负重训练接口 ===
class AnaerobicLogCreate(BaseModel):
    exercise_name: str
    weight: float
    sets: int
    reps: int
    date: Optional[str] = None
    category: Optional[str] = None

class AnaerobicLogResponse(BaseModel):
    id: int
    date: str
    exercise_name: str
    weight: float
    sets: int
    reps: int
    category: Optional[str] = None

@app.get("/api/anaerobic", response_model=list[AnaerobicLogResponse])
def get_anaerobic_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from models import AnaerobicLog
    logs = db.query(AnaerobicLog).filter(AnaerobicLog.user_id == current_user.id).order_by(AnaerobicLog.date.desc(), AnaerobicLog.id.desc()).limit(30).all()
    return logs

@app.post("/api/anaerobic", response_model=AnaerobicLogResponse)
def add_anaerobic_log(item: AnaerobicLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from models import AnaerobicLog
    today = item.date or get_beijing_now().date().isoformat()
    new_log = AnaerobicLog(
        date=today,
        exercise_name=item.exercise_name,
        weight=item.weight,
        sets=item.sets,
        reps=item.reps,
        category=item.category,
        user_id=current_user.id
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log
