from models.record.base import Record
from datetime import datetime, date as dt_date, time as dt_time
from bson import ObjectId

class DietRecord(Record):
    def __init__(self, food_name, amount, pet_id,time_str, date=None, _id=None):
        super().__init__(date, _id)
        self.food_name = food_name
        self.amount = int(amount)
        self.pet_id = pet_id
        self.time_str = self._format_date_str(time_str)
        self.date = datetime.fromisoformat(date) if isinstance(date, str) else date or datetime.now() 
        self._id = _id

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

    def view_record(self):
        return f"{self.date.date()} 飼料: {self.food_name}, 時間:{self.time_str} ,量: {self.amount}"

    def update_record(self, food_name=None, amount=None,time_str=None):
        if food_name:
            self.food_name = food_name
        if amount is not None:
            self.amount = amount
        if time_str:
            self.date = time_str

    def to_dict(self):
        return {
            "_id": self._id if self._id else ObjectId(),
            "type": "diet",
            "date": self.date.isoformat(),
            "time_str": self.time_str,
            "food_name": self.food_name,
            "amount": self.amount,
            "pet_id": self.pet_id
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            food_name=data.get("food_name"),
            amount=data.get("amount"),
            time_str=data.get("time_str"),
            pet_id=data.get("pet_id"),
            date=data.get("date"),
            _id=data.get("_id")
        )
