# Garmin Connect API 开发参考指南 (基于 python-garminconnect)

本文档整理自 `python-garminconnect` 库的源码和示例，旨在为你的其他项目提供一个清晰、完整的佳明 API 集成参考。
项目地址：https://github.com/cyberjunky/python-garminconnect.git  

## 1. 安装与依赖

```bash
pip install garminconnect
# 还需要安装 garth 和 requests，但在安装 garminconnect 时会自动获取配套依赖
# 如果需要处理特定的认证异常，可能需要直接引入 garth
```

## 2. 核心认证机制与客户端初始化

该库目前使用 `garth` 作为底层的 OAuth 模拟框架。**最核心的设计理念是：仅进行一次账密登录，之后持久化存储令牌 (Tokens)，避免频繁登录导致被封号或遇到频繁拉起 MFA 验证。**

### 2.1 初始化与登录策略

```python
import os
from pathlib import Path
from garminconnect import Garmin, GarminConnectAuthenticationError
from garth.exc import GarthHTTPError

def init_garmin_client(email, password, token_dir="~/.garminconnect"):
    """
    初始化并登录 Garmin 客户端
    策略：优先使用本地 Token 缓存，失败后再使用账密登录，登录成功后重新缓存 Token
    """
    tokenstore_path = Path(token_dir).expanduser()
    
    # 1. 尝试使用 Token 登录
    try:
        garmin = Garmin()
        garmin.login(str(tokenstore_path))
        print("✅ 使用本地 Token 登录成功")
        return garmin
    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        print("⚠️ 未找到有效 Token 或 Token 已失效，尝试使用账密登录...")

    # 2. 账密登录
    garmin = Garmin(email=email, password=password, is_cn=True) # 如果使用佳明中国区账号，务必设置 is_cn=True
    
    # 尝试登录并处理 MFA（如开启了多因素认证）
    # return_on_mfa=True 的作用是遇到 MFA 时先挂起
    garmin.return_on_mfa = True 
    result1, result2 = garmin.login()
    
    if result1 == "needs_mfa":
        mfa_code = input("请输入已发送至你设备的 MFA 验证码: ")
        # 恢复登录流程
        garmin.resume_login(result2, mfa_code)

    # 3. 登录成功后将最新的 Token 固化到本地目录
    os.makedirs(tokenstore_path, exist_ok=True)
    garmin.garth.dump(str(tokenstore_path))
    print("✅ 账密登录成功，已保存新的 Token！")
    
    return garmin
```

> **注意：** 使用国内域名的佳明账号时（garmin.cn），在实例化时必须设置 `is_cn=True`。

## 3. 核心 API 接口指南

所有的接口调用基本都依赖于 `Garmin` 实例。日期参数通常要求 `YYYY-MM-DD` 格式的字符串。

### 3.1 用户基础信息

```python
# 获取用户全名
full_name = garmin.get_full_name()

# 获取系统设定的度量单位 (如：metric 公制, statute 英制)
unit_system = garmin.get_unit_system()
```

### 3.2 每日基础与健康数据 (Daily Stats)

绝大多数基础数据的拉取只需要当天的日期字符串：
```python
from datetime import date
today = date.today().isoformat()  # e.g., '2023-10-15'

# 获取每日总览（包含步数、距离、卡路里、卡路里消耗目标等综合数据）
# 返回字典包含：totalSteps, totalDistanceMeters, totalKilocalories, floorsClimbed 等
summary = garmin.get_user_summary(today)

# 获取步数趋势图表数据（当天不同时段详细步数）
steps_data = garmin.get_steps_data(today)

# 获取水份补充量记录
# 返回字典包含：valueInML（摄入的水量）, goalInML（目标量）
hydration = garmin.get_hydration_data(today)

# 获取单日心率详细数据流 (全天心率图表)
heart_rates = garmin.get_heart_rates(today)

# 获取睡眠基本信息（包含深睡、浅睡、REM、觉醒次数时间等）
sleep_data = garmin.get_sleep_data(today)

# 获取当日身体电量数据流
body_battery = garmin.get_body_battery(today)

# 获取压力指标
stress_data = garmin.get_stress_data(today)

# 单日高阶综合版（包含身体成分，例如脂肪率和上述基础数据字典整合）
stats_and_body = garmin.get_stats_and_body(today)
```

### 3.3 历史数据与聚合查询

部分接口支持拉取连续的或聚合的数据（API对大跨度可能有 28 天的硬限制，但底层库已自动做了分片处理）：

```python
start_date = '2023-09-01'
end_date = '2023-09-30'

# 批量获取多日步数统计
daily_steps_range = garmin.get_daily_steps(start_date, end_date)

# 按“周”进行数据聚合查询
# end_date: 终止日期，weeks: 往前推几周的聚合数据（包含总步数，平均每日步数等）
weekly_steps = garmin.get_weekly_steps(end=end_date, weeks=4)
weekly_stress = garmin.get_weekly_stress(end=end_date, weeks=4)
weekly_intensity = garmin.get_weekly_intensity_minutes(start=start_date, end=end_date)
```

### 3.4 运动与赛事数据 (Activities & Workouts)

针对特定的跑步、骑行等单次独立活动。

```python
# 1. 列表查询：获取最近的运动列表
# 参数：start：偏移量下标, limit：数量限制 (最大通常设为 1000)
activities = garmin.get_activities(start=0, limit=10)

# 对提取出来的每一个 activity 遍历
for activity in activities:
    activity_id = activity.get("activityId")
    activity_name = activity.get("activityName")
    duration = activity.get("duration") # 秒
    distance = activity.get("distance") # 米
    
    # 2. 根据运动 ID 获取单次运动的极致详细数据字典（配速分段、圈数、平均参数）
    details = garmin.get_activity(activity_id)
    
    # 3. 下载标准格式运动源文件 (.FIT / .TCX / .GPX) [适用于将数据转移至其他平台]
    # 需要传递保存到本地的方法
    fit_binary = garmin.download_activity(activity_id, dl_fmt=garmin.ActivityDownloadFormat.FIT)
    with open(f"{activity_id}.fit", "wb") as f:
        f.write(fit_binary)
```

### 3.5 身体指标与设备数据

```python
# 获取最大摄氧量记录 (VO2 Max)
vo2max = garmin.get_max_metrics(today)

# 获取 HRV (心率变异性)
hrv = garmin.get_hrv_data(today)

# 获取你账号关联的所有设备列表及基本属性
devices = garmin.get_devices()

# 获取体成分属性（如果接入了佳明的体脂秤或自己同步过）
body_composition = garmin.get_body_composition(start_date, end_date)
```

## 4. 最佳实践与错误处理规范

在自建新项目时，强烈建议对 `python-garminconnect` 的方法外层包一层重试或统一错误捕获：

这是项目 `example.py` 推荐的做法：

```python
from garth.exc import GarthHTTPError
from garminconnect import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError
)

def safe_garmin_call(method, *args, **kwargs):
    """一个通用的捕获包装器"""
    try:
        return method(*args, **kwargs)
    except GarthHTTPError as e:
        status_code = getattr(getattr(e, "response", None), "status_code", None)
        if status_code == 400:
            print("❌ 请求格式错误")
        elif status_code in (401, 403):
            print("❌ 凭证失效或是没权限，请重新登录！")
            # 在这里可以触发重新登录和 token 更新的钩子
        elif status_code == 429:
            print("❌ 请求过于频繁，触发了佳明的速率限制机制。")
        else:
            print(f"❌ 服务器 HTTP 异常: {e}")
    except FileNotFoundError:
        print("❌ 未发现登录凭证 Token...")
    except GarminConnectAuthenticationError as e:
        print(f"❌ 认证异常: {e}")
    except GarminConnectTooManyRequestsError as e:
        print(f"❌ 请求过于频繁 (API层): {e}")
    except GarminConnectConnectionError as e:
        print(f"❌ 连接被断开: {e}")
    except Exception as e:
        print(f"❌ 发生意外报错: {e}")
    return None

# 使用方法:
# safe_garmin_call(garmin.get_steps_data, today)
```

### 注意事项：
1. **防止风控**：获取大时间跨度数据时（比如全年心率），一定要**加入循环休眠（Sleep）**。由于佳明并未公开这些 API 服务边界，高并发极易触发 429 降级或直接阻断你的 IP 取数据权限。
2. **下载原文件 `dl_fmt` 枚举：** 注意下载 GPX/FIT 文件时，方法中的 `dl_fmt` 参数应当使用枚举 `garmin.ActivityDownloadFormat.FIT`，而不是字符串。
