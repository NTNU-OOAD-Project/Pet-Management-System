from models.record.base import Record

class DietRecord(Record):
    def __init__(self, food_name, amount, date=None):
        super().__init__(date)
        self.food_name = food_name
        self.amount = amount

    def view_record(self):
        return f"{self.date} 飼料: {self.food_name}, 量: {self.amount}"

    def update_record(self, food_name=None, amount=None):
        if food_name:
            self.food_name = food_name
        if amount:
            self.amount = amount

    def to_dict(self):
        return {
            "id": self.id,
            "type": "diet",
            "date": self.date.isoformat(),
            "food_name": self.food_name,
            "amount": self.amount
        }
