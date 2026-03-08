import os
from pathlib import Path
from garminconnect import Garmin, GarminConnectAuthenticationError
from garth.exc import GarthHTTPError

def init_garmin_client(email=None, password=None, token_dir="~/.garminconnect"):
    """
    初始化并登录 Garmin 客户端
    按照需求：优先尝试本地 Token 登录。如果不成功且传入了账密，则手动交互登录。
    """
    tokenstore_path = Path(token_dir).expanduser()
    
    # 尝试使用 Token 登录
    try:
        garmin = Garmin()
        garmin.login(str(tokenstore_path))
        print("✅ 使用本地 Token 登录成功")
        return garmin
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        print("⚠️ 未找到有效 Token 或 Token 已失效...")
        
    if not email or not password:
        raise ValueError("Token 无效且未提供账号密码进行重新登录。")

    # 账密登录
    print("正在尝试使用账密登录...")
    garmin = Garmin(email=email, password=password, is_cn=True) # 使用佳明中国区
    
    garmin.login()

    os.makedirs(tokenstore_path, exist_ok=True)
    garmin.garth.dump(str(tokenstore_path))
    print("✅ 账密登录成功，已保存新的 Token！")
    
    return garmin

# 包装器示例
def safe_garmin_call(method, *args, **kwargs):
    try:
        return method(*args, **kwargs)
    except Exception as e:
        print(f"❌ 发生报错: {e}")
        return None
