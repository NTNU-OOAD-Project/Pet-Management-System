from models.record.base import Record
from datetime import datetime

class HealthRecord(Record):
    def __init__(self, details, vaccine, date=None, _id=None):
        super().__init__(date)
        self.details = details
        self.vaccine = vaccine
        self._id = _id  # MongoDB 對應用

    def view_record(self):
        return f"{self.date} 健康狀況: {self.details}, 疫苗: {self.vaccine}"

    def update_record(self, details=None, vaccine=None):
        if details:
            self.details = details
        if vaccine:
            self.vaccine = vaccine

    def to_dict(self):
        return {
            "type": "health",
            "date": self.date.isoformat(),
            "details": self.details,
            "vaccine": self.vaccine
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            details=data.get("details"),
            vaccine=data.get("vaccine"),
            date=datetime.fromisoformat(data["date"]) if "date" in data else None,
            _id=data.get("_id")
        )
