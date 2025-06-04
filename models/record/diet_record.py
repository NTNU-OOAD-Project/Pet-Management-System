from models.record.base import Record
from datetime import datetime
from bson import ObjectId

class DietRecord(Record):
    def __init__(self, food_name=None, amount=None, pet_id=None, date=None, end_date=None, _id=None):
        super().__init__(date, _id)
        self.food_name = food_name
        self.amount = amount
        self.pet_id = pet_id
        self.date = datetime.fromisoformat(date) if isinstance(date, str) else date or datetime.now()
        self.end_date = datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date
        self._id = _id
        self.db = None

    def add_diet_record(self, food_name, amount, pet_id, date=None, end_date=None):
        if self.db is None:
            raise RuntimeError("請先設定 db 屬性")

        new_record = {
            "_id": str(ObjectId()),
            "food_name": food_name,
            "amount": amount,
            "date": date,
            "end_date": end_date
        }

        result = self.db.users.update_one(
            {"pets.pet_id": pet_id},
            {"$push": {"pets.$.diet_records": new_record}}
        )

        if result.modified_count == 0:
            raise ValueError(f"找不到 pet_id={pet_id} 或無法新增飲食紀錄")

        return new_record

    # 補上這兩個抽象方法實作
    def update_record(self, **kwargs):
        if 'food_name' in kwargs:
            self.food_name = kwargs['food_name']
        if 'amount' in kwargs:
            self.amount = kwargs['amount']
        if 'date' in kwargs:
            d = kwargs['date']
            self.date = datetime.fromisoformat(d) if isinstance(d, str) else d
        if 'end_date' in kwargs:
            ed = kwargs['end_date']
            self.end_date = datetime.fromisoformat(ed) if isinstance(ed, str) else ed

    def view_record(self):
        return f"{self.date.date()} 飼料: {self.food_name}, 量: {self.amount}"

    def to_dict(self):
        d = {
            "_id": self._id if self._id else ObjectId(),
            "type": "diet",
            "date": self.date.isoformat(),
            "food_name": self.food_name,
            "amount": self.amount,
            "pet_id": self.pet_id,
        }
        if self.end_date:
            d["end_date"] = self.end_date.isoformat() if isinstance(self.end_date, datetime) else self.end_date
        return d

    @classmethod
    def from_dict(cls, data: dict):
        food_name = data.get("food_name")
        amount = data.get("amount")
        pet_id = data.get("pet_id")
        date = data.get("date")
        end_date = data.get("end_date")
        _id = data.get("_id")

        if food_name is None or amount is None or pet_id is None:
            raise ValueError("DietRecord 缺少必要欄位 food_name, amount 或 pet_id")

        return cls(
            food_name=food_name,
            amount=amount,
            pet_id=pet_id,
            date=date,
            end_date=end_date,
            _id=_id
        )
