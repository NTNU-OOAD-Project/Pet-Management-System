from models.record.base import Record
from datetime import datetime

class DietRecord(Record):
    def __init__(self, food_name, amount, date=None, _id=None):
        super().__init__(date)
        self.food_name = food_name
        self.amount = amount
        self._id = _id  # MongoDB 對應用

    def view_record(self):
        return f"{self.date} 飼料: {self.food_name}, 量: {self.amount}"

    def update_record(self, food_name=None, amount=None):
        if food_name:
            self.food_name = food_name
        if amount:
            self.amount = amount

    def to_dict(self):
        return {
            "type": "diet",
            "date": self.date.isoformat(),
            "food_name": self.food_name,
            "amount": self.amount
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            food_name=data.get("food_name"),
            amount=data.get("amount"),
            date=datetime.fromisoformat(data["date"]) if "date" in data else None,
            _id=data.get("_id")
        )
