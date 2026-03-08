from sqlalchemy import Boolean, Column, Integer, String, Date, Text

from .database import Base

class UserConfig(Base):
    __tablename__ = "user_config"

    id = Column(Integer, primary_key=True, index=True)
    target_kcal = Column(Integer, default=2000)
    garmin_user = Column(String, nullable=True)
    garmin_pass = Column(String, nullable=True)

class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    date = Column(String, primary_key=True, index=True) # YYYY-MM-DD
    active_kcal = Column(Integer, default=0)
    resting_kcal = Column(Integer, default=0)
    steps = Column(Integer, default=0)
    sleep_minutes = Column(Integer, default=0)

class FoodLogs(Base):
    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True) # YYYY-MM-DD
    food_name = Column(String)
    kcal = Column(Integer)
    macros = Column(Text) # JSON string
    img_path = Column(String, nullable=True)
