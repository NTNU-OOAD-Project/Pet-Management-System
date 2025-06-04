from models.record.base import Record
from datetime import datetime, date as dt_date, time as dt_time
from bson import ObjectId

class CareReminderRecord(Record):
    def __init__(self, message, daily : bool , pet_id, time_str ,date=None, _id=None,active=True):
        super().__init__(date, _id)
        self.message = message
        self.daily = daily 
        self.time_str = self._format_time_str(time_str)  # 格式為 "HH:MM:SS"
        self.pet_id = pet_id
        self._id = _id
        self.date = datetime.fromisoformat(date) if isinstance(date, str) else date or datetime.now() 
        self.active = active       


    def _format_time_str(self, t):
        if isinstance(t, dt_time):
            return t.strftime("%H:%M")
        elif isinstance(t, str):
            # 嘗試 parse，保證是 HH:MM[:SS]
            return datetime.strptime(t, "%H:%M" if len(t) == 5 else "%H:%M:%S").time().strftime("%H:%M")
        raise ValueError("無效的 time_str 格式")



    def view_record(self):
        return f"{self.date.date()} 照護提醒: {self.message}, 時間: {self.time_str}, 類型: {self.reminder_type}"

    def update_record(self, message=None, reminder_type=None, time_str=None):
        if message:
            self.message = message
        if reminder_type:
            self.reminder_type = reminder_type
        if time_str:
            self.time_str = time_str

    def to_dict(self):
        return {
            "_id": self._id if self._id else ObjectId(),
            "type": "remind",
            "message": self.message,
            "daily": self.daily,
            "time_str": self.time_str,
            "pet_id": self.pet_id,
            "active": self.active
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            message=data.get("message"),
            daily=data.get("daily"),
            time_str=data.get("time_str"),
            pet_id=data.get("pet_id"),
            _id=data.get("_id"),
            active=data.get("active", True)
        )