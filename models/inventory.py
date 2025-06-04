from models.record.inventory_record import InventoryRecord
from bson import ObjectId
class Inventory:
    def __init__(self, item_name, quantity=0, threshold=10, records=None):
        self.item_name = item_name
        self.quantity = int(quantity)
        self.threshold = int(threshold)
        self.records = records if records is not None else []

    def is_below_threshold(self) -> bool:
        return self.quantity < self.threshold

    def to_dict(self) -> dict:
        return {
            "item_name": self.item_name,
            "quantity": self.quantity,
            "threshold": self.threshold,
            "records": [r.to_dict() for r in self.records] if self.records else []
        }

    @classmethod
    def from_dict(cls, data: dict):
        records_data = data.get("records", [])
        records = [InventoryRecord.from_dict(r) for r in records_data]
        return cls(
            item_name=data["item_name"],
            quantity=data.get("quantity", 0),
            threshold=data.get("threshold", 10),
            records=records,
        )

    def view_status(self) -> str:
        status = "⚠️ 低庫存警告" if self.is_below_threshold() else "✅ 正常"
        return f"{self.item_name}：{self.quantity}（警戒線 {self.threshold}）{status}"

    @classmethod
    def update_threshold_by_item_name(cls, db, user_id: str, item_name: str, new_threshold: float):
        result = db.users.update_one(
            {
                "_id": ObjectId(user_id),
                "inventory.item_name": item_name
            },
            {
                "$set": {"inventory.$.threshold": new_threshold}
            }
        )
        if result.modified_count > 0:
            print(f"🟢 [{item_name}] 警戒線已更新為 {new_threshold}")
        else:
            raise ValueError(f"❌ 找不到 [{item_name}] 或警戒線未變更")

    def save_to_db(self, db):
        db.inventory.update_one(
            {"item_name": self.item_name},
            {"$set": self.to_dict()},
            upsert=True
        )

    @classmethod
    def from_db(cls, db, item_name):
        data = db.inventory.find_one({"item_name": item_name})
        return cls.from_dict(data) if data else None

    @classmethod
    def exists_in_db(cls, db, item_name) -> bool:
        return db.inventory.count_documents({"item_name": item_name}) > 0

    def delete_from_db(self, db):
        db.inventory.delete_one({"item_name": self.item_name})

    # ✅ 新增：加入至使用者的 inventory 陣列
    def add_to_user_inventory(self, db, user_id: str):
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"inventory": self.to_dict()}}
        )
        if result.modified_count > 0:
            print(f"✅ 成功加入 [{self.item_name}] 至使用者 {user_id} 的存貨清單")
        else:
            raise ValueError("❌ 加入失敗，可能找不到使用者")

    # ✅ 新增：從使用者的 inventory 陣列中移除指定項目
    def delete_from_user_inventory(self, db, user_id: str):
        result = db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"inventory": {"item_name": self.item_name}}}
        )
        if result.modified_count > 0:
            print(f"🗑️ 已從使用者 {user_id} 的 inventory 中刪除 [{self.item_name}]")
        else:
            raise ValueError("❌ 刪除失敗，可能找不到該項目或使用者")
