import secrets
import sys
sys.path.append("/Users/wanglianzuo/health/backend")
from database import SessionLocal
from models import User, UserConfig
from core.auth import create_access_token

db = SessionLocal()
try:
    # 查找或创建一个测试用户
    u = db.query(User).filter(User.username == "test_autofill_config").first()
    if not u:
        u = User(username="test_autofill_config", hashed_password="hashed")
        db.add(u)
        db.commit()
    
    # 模拟请求
    config = db.query(UserConfig).filter(UserConfig.user_id == u.id).first()
    if config:
        db.delete(config)
        db.commit()
    
    # 初始化
    config = UserConfig(user_id=u.id)
    db.add(config)
    db.commit()
    
    # 模拟 POST 请求更新
    config.height = 175.0
    config.weight = 70.0
    config.age = 25
    config.gender = "male"
    db.commit()
    
    # 再次查询验证
    verify = db.query(UserConfig).filter(UserConfig.user_id == u.id).first()
    print("Updated height:", verify.height)
    print("Updated weight:", verify.weight)
    
except Exception as e:
    print("Error:", str(e))
finally:
    db.close()
