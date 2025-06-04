from models.record.base import Record
from datetime import datetime, date as dt_date, time as dt_time
from bson import ObjectId

class InventoryRecord(Record):
    def __init__(self, item_name, time_str , delta_quantity, reason, user_id=None, date=None, _id=None):
        super().__init__(date)
        self.item_name = item_name              # 品項名稱
        self.delta_quantity = int(delta_quantity)    # 加(+)、減(-)
        self.reason = reason                    # 例如：進貨、食用、報廢
        self.user_id = user_id
        self.date = datetime.fromisoformat(date) if isinstance(date, str) else date or datetime.now()              
        self._id = _id
        self.time_str = time_str

    def update_record(self, item_name=None, delta_quantity=None, reason=None,date=None):
        if item_name:
            self.item_name = item_name
        if delta_quantity is not None:
            self.delta_quantity = delta_quantity
        if reason:
            self.reason = reason
        if date:
            self.date = datetime.fromisoformat(date) if isinstance(date, str) else date

    def _format_date_str(self, t):
        if isinstance(t, dt_date):  # 可支援 date 和 datetime
            return t.strftime("%Y-%m-%d")
        elif isinstance(t, str):
            try:
                # 自動判斷是否為完整日期格式
                fmt = "%Y-%m-%d" if len(t) == 10 else "%Y/%m/%d"
                return datetime.strptime(t, fmt).date().strftime("%Y-%m-%d")
            except ValueError:
                raise ValueError(f"無效的日期字串: {t}")
        raise ValueError("無效的日期格式輸入")


    def to_dict(self):
        return {
            "_id": self._id if self._id else ObjectId(),
            "type": "inventory",
            "date": self.date.isoformat(),
            "item_name": self.item_name,
            "delta_quantity": self.delta_quantity,
            "reason": self.reason,
            "user_id": self.user_id,
            "time_str": self.time_str
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            item_name=data["item_name"],
            delta_quantity=data["delta_quantity"],
            reason=data["reason"],
            user_id=data.get("user_id"),
            date=data.get("date"),
            _id=data.get("_id"),
            time_str=data.get("time_str")
        )

    def view_record(self):
        sign = "+" if self.delta_quantity > 0 else ""
        return f"{self.date.date()} | {self.item_name} {sign}{self.delta_quantity} ({self.reason})"
