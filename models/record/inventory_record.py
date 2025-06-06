from models.record.base import Record
from datetime import datetime
from bson import ObjectId

class InventoryRecord(Record):
    def __init__(self, item_name, delta_quantity, reason, user_id=None, date=None, _id=None):
        super().__init__(date, _id)
        self.item_name = item_name              # 品項名稱
        self.delta_quantity = delta_quantity    # 加(+)、減(-)
        self.reason = reason                    # 例如：進貨、食用、報廢
        self.user_id = user_id
        self.date = datetime.fromisoformat(date) if isinstance(date, str) else date or datetime.now()
        self._id = _id  # 由外部傳入

    def update_record(self, item_name=None, delta_quantity=None, reason=None, date=None):
        if item_name:
            self.item_name = item_name
        if delta_quantity is not None:
            self.delta_quantity = delta_quantity
        if reason:
            self.reason = reason
        if date:
            self.date = datetime.fromisoformat(date) if isinstance(date, str) else date

    def to_dict(self):
        # _id 須由外部確保有值
        return {
            "_id": self._id,
            "type": "inventory",
            "date": self.date.isoformat(),
            "item_name": self.item_name,
            "delta_quantity": self.delta_quantity,
            "reason": self.reason,
            "user_id": self.user_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            item_name=data["item_name"],
            delta_quantity=data["delta_quantity"],
            reason=data["reason"],
            user_id=data.get("user_id"),
            date=data.get("date"),
            _id=data.get("_id")
        )

    def view_record(self):
        sign = "+" if self.delta_quantity > 0 else ""
        return f"{self.date.date()} | {self.item_name} {sign}{self.delta_quantity} ({self.reason})"