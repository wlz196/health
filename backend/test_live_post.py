import sys
import requests
sys.path.append("/Users/wanglianzuo/health/backend")
from database import SessionLocal
from models import User

db = SessionLocal()
try:
    u = db.query(User).filter(User.username == "test_overview_post").first()
    if not u:
        u = User(username="test_overview_post", hashed_password="hashed")
        db.add(u)
        db.commit()

    from core.auth import create_access_token
    token = create_access_token(data={"sub": u.username})

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "height": 175,
        "weight": 70,
        "age": 25,
        "bmr_kcal": 1600,
        "gender": "male",
        "activity_multiplier": 1.2
    }

    res = requests.post("http://127.0.0.1:8080/api/config", json=payload, headers=headers)
    print("POST /api/config response:", res.text)

    res2 = requests.get("http://127.0.0.1:8080/api/overview", headers=headers)
    print("GET /api/overview response:", res2.text)

except Exception as e:
    print("Error:", str(e))
finally:
    db.close()
