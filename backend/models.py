from sqlalchemy import Boolean, Column, Integer, String, Date, Text, Float

from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class UserConfig(Base):
    __tablename__ = "user_config"

    id = Column(Integer, primary_key=True, index=True)
    target_kcal = Column(Integer, default=2000)
    garmin_user = Column(String, nullable=True)
    garmin_pass = Column(String, nullable=True)
    bmr_kcal = Column(Integer, default=1500)
    
    # 🌟 新增公式测算支撑
    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True) # 'male' / 'female'
    activity_multiplier = Column(Float, default=1.2)
    user_id = Column(Integer, index=True) # 🌟 绑定用户

class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    date = Column(String, primary_key=True, index=True) # YYYY-MM-DD
    active_kcal = Column(Integer, default=0)
    resting_kcal = Column(Integer, default=0)
    steps = Column(Integer, default=0)
    sleep_minutes = Column(Integer, default=0)
    user_id = Column(Integer, index=True) # 🌟 绑定用户

class FoodLogs(Base):
    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True) # YYYY-MM-DD
    time = Column(String, nullable=True) # HH:MM
    food_name = Column(String)
    kcal = Column(Integer)
    macros = Column(Text) # JSON string
    img_path = Column(String, nullable=True)
    user_id = Column(Integer, index=True) # 🌟 绑定用户

class SavedFood(Base):
    __tablename__ = "saved_food"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    kcal = Column(Integer)
    protein = Column(Float, default=0.0)
    fat = Column(Float, default=0.0)
    carb = Column(Float, default=0.0)
    is_per_100g = Column(Boolean, default=False)  # 🌟 是否为100g配料表模板
    user_id = Column(Integer, index=True) # 🌟 绑定用户

class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True) # YYYY-MM-DD
    weight = Column(Float)
    day_type = Column(String, nullable=True) # 🌟 绑定今日运动模式
    user_id = Column(Integer, index=True) # 🌟 绑定用户

class AnaerobicLog(Base):
    __tablename__ = "anaerobic_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True) # YYYY-MM-DD
    exercise_name = Column(String)
    weight = Column(Float) # 重量 kg
    sets = Column(Integer) # 组数
    reps = Column(Integer) # 次数
    category = Column(String, nullable=True) # 🌟 动作二分化分类，如 '上半身', '下半身'
    user_id = Column(Integer, index=True) # 🌟 绑定用户
