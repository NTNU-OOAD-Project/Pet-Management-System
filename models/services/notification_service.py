from datetime import datetime
from bson import ObjectId

class NotificationService:
    def __init__(self, db):
        self.collection = db['notifications']

    def add_notification(self, user_id, message, type="GENERAL"):
        self.collection.insert_one({
            "user_id": ObjectId(user_id) if isinstance(user_id, str) else user_id,
            "message": message,
            "type": type,
            "is_read": False,
            "timestamp": datetime.now()
        })

    def get_all_notifications(self, user_id):
        return list(self.collection.find(
            {"user_id": ObjectId(user_id)},
            sort=[("timestamp", -1)]
        ))

    def get_unread_count(self, user_id):
        return self.collection.count_documents({
            "user_id": ObjectId(user_id),
            "is_read": False
        })

    def mark_as_read(self, notification_id):
        self.collection.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"is_read": True}}
        )

    def mark_all_as_read(self, user_id):
        self.collection.update_many(
            {"user_id": ObjectId(user_id), "is_read": False},
            {"$set": {"is_read": True}}
        )