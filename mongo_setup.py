from pymongo import MongoClient
from werkzeug.security import generate_password_hash

client = MongoClient("mongodb://localhost:27017/")
db = client["pet_db"]
users_col = db["users"]

print("🔗 實際連線 URI：", client)

# 測試用使用者資料
user_data = {
    "_id": "u001",
    "name": "Alice",
    "email": "alice@example.com",
    "phone": "0912345678",
    "password": generate_password_hash("test1234"),
    "inventory": {
        "inventory": {
            "DogFood": 3.0,
            "CatFood": 2.0
        },
        "thresholds": {
            "DogFood": 1.0,
            "CatFood": 1.5
        }
    },
    "pets": []
}

# 重建
users_col.delete_many({"_id": "u001"})
result = users_col.insert_one(user_data)

print("✅ 使用者已建立：", result.inserted_id)
