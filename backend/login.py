import os
from pathlib import Path
from garminconnect import Garmin
from garth.exc import GarthHTTPError
from core.garmin_client import init_garmin_client

def manual_login():
    """
    提供给用户的独立交互式登录脚本，它将会引导用户输入账密和可能出现的 MFA 并持久化缓存。
    """
    print("=" * 50)
    print("Garmin Connect 交互式登录小工具")
    print("=" * 50)
    print("请输入你的 Garmin (佳明中国) 账号和密码。")
    print("注意: 你的密码只会在本地运行并通过官方库和 Garmin 接口交互，不会被储存在代码中。\n")
    
    email = input("邮箱帐号: ")
    password = input("密码: ")
    
    # 强制清理可能的旧缓存，确保全新的账密生效
    token_dir = os.path.expanduser("~/.garminconnect")
    
    try:
        # 调用我们在 core 里面写的复用函数
        client = init_garmin_client(email, password, token_dir)
        print("\n✅ 登录流程完成！如果上述未报错，说明 Token 已成功接管。")
        print("您现在可以关闭此脚本了。后端将自动读取 ~/.garminconnect 中的凭证。")
        
        # 测试一下是否能拿到真名
        print(f"👉 登陆者全名: {client.get_full_name()}")
        
    except Exception as e:
        print(f"\n❌ 登录过程中发生了致命错误: {e}")

if __name__ == "__main__":
    manual_login()
