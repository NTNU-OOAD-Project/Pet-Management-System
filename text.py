from pymongo import MongoClient
from dotenv import load_dotenv
from services.record_manager import RecordManager
import os

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("MONGODB_DB")]

rm = RecordManager()

# ✅ 準備資料
reminder_data = {
    "daily": True,
    "time_str": "08:00",
    "message": "早上餵藥",
    "pet_id": "683ec35b62de324bf9cb1b44",
}

# ✅ 新增 type_str 為 care_remind 的紀錄
try:
    record = rm.add_record_by_type("remind", reminder_data, db)
    print("✅ 成功新增：", record.to_dict())
except Exception as e:
    print("❌ 發生錯誤：", e)
user_id = "683d8676e35c1796af94e22a"
recode=rm.view_by_type(db,"683ed5fa2a94ae3f8f2fc691","remind")

