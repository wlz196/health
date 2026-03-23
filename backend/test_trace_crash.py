import sys
sys.path.append("/Users/wanglianzuo/health/backend")
from database import SessionLocal
from models import User
from main import get_daily_overview

db = SessionLocal()
try:
    u = db.query(User).filter(User.username == "test_overview_post").first()
    if not u:
        print("User not found from previous test")
    else:
        print("Running over metrics for user ID:", u.id)
        res = get_daily_overview(db=db, current_user=u)
        print("Success:", res)

except Exception as e:
    import traceback
    print("--- CRASH DETECTED ---")
    traceback.print_exc()
finally:
    db.close()
