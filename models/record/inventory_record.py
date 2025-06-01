from models.record.base import Record
from datetime import datetime

class InventoryRecord(Record):
    def __init__(self, item_name, delta_quantity, reason, date=None, _id=None):
        super().__init__(date)
        self.item_name = item_name              # 品項名稱
        self.delta_quantity = delta_quantity    # 加(+)、減(-)
        self.reason = reason                    # 例如：進貨、食用、報廢
        self._id = _id                          # MongoDB 對應用

    def update_record(self, item_name=None, delta_quantity=None, reason=None):
        if item_name:
            self.item_name = item_name
        if delta_quantity is not None:
            self.delta_quantity = delta_quantity
        if reason:
            self.reason = reason

    def to_dict(self):
        return {
            "type": "inventory_record",
            "date": self.date.isoformat(),
            "item_name": self.item_name,
            "delta_quantity": self.delta_quantity,
            "reason": self.reason
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            item_name=data["item_name"],
            delta_quantity=data["delta_quantity"],
            reason=data["reason"],
            date=datetime.fromisoformat(data["date"]) if "date" in data else None,
            _id=data.get("_id")
        )

    def view_record(self):
        sign = "+" if self.delta_quantity > 0 else ""
        return f"{self.date.date()} | {self.item_name} {sign}{self.delta_quantity} ({self.reason})"
