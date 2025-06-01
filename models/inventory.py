class Inventory:
    def __init__(self, item_name, quantity=0, threshold=10, _id=None):
        self.item_name = item_name
        self.quantity = quantity
        self.threshold = threshold
        self._id = _id

    def is_below_threshold(self) -> bool:
        return self.quantity < self.threshold

    def to_dict(self) -> dict:
        return {
            "item_name": self.item_name,
            "quantity": self.quantity,
            "threshold": self.threshold
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            item_name=data["item_name"],
            quantity=data.get("quantity", 0),
            threshold=data.get("threshold", 10),
            _id=data.get("_id")
        )

    def view_status(self) -> str:
        status = "⚠️ 低庫存警告" if self.is_below_threshold() else "✅ 正常"
        return f"{self.item_name}：{self.quantity}（警戒線 {self.threshold}）{status}"

    def set_threshold(self, new_threshold: float, db):
        self.threshold = new_threshold
        self.save_to_db(db)

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
