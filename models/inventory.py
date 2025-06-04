from models.record.inventory_record import InventoryRecord
from bson import ObjectId
class Inventory:
    def __init__(self, item_name, quantity=0, threshold=10, records=None):
        self.item_name = item_name
        self.quantity = int(quantity)
        self.threshold = int(threshold)
        self.records = records if records is not None else []  # 儲存 InventoryRecord 的 list

    def is_below_threshold(self) -> bool:
        return self.quantity < self.threshold

    def to_dict(self) -> dict:
        return {
            "item_name": self.item_name,
            "quantity": self.quantity,
            "threshold": self.threshold
        }

    @staticmethod
    def delete_by_id(db, inventory_id: str):
        result = db.inventory.delete_one({"_id": ObjectId(inventory_id)})
        if result.deleted_count == 0:
            raise ValueError("找不到指定的 inventory_id")


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
            print(f"✅ [{item_name}] 警戒線已更新為 {new_threshold}")
        else:
            raise ValueError(f"找不到 {item_name} 或警戒線未變更")
    


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
