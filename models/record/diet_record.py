from models.record.base import Record
from datetime import datetime
from bson import ObjectId

class DietRecord(Record):
    def __init__(self, food_name, amount, pet_id, date=None, _id=None):
        super().__init__(date, _id)
        self.food_name = food_name
        self.amount = amount
        self.pet_id = pet_id
        self.date = datetime.fromisoformat(date) if isinstance(date, str) else date or datetime.now()
        self._id = _id

    def view_record(self):
        return f"{self.date.date()} 飼料: {self.food_name}, 量: {self.amount}"

    def update_record(self, food_name=None, amount=None,date=None):
        if food_name:
            self.food_name = food_name
        if amount is not None:
            self.amount = amount
        if date:
            self.date = datetime.fromisoformat(date) if isinstance(date, str) else date

    def to_dict(self):
        return {
            "_id": self._id if self._id else ObjectId(),
            "type": "diet",
            "date": self.date.isoformat(),
            "food_name": self.food_name,
            "amount": self.amount,
            "pet_id": self.pet_id
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            food_name=data.get("food_name"),
            amount=data.get("amount"),
            pet_id=data.get("pet_id"),
            date=data.get("date"),
            _id=data.get("_id")
        )