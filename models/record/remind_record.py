from models.record.base import Record
from datetime import datetime, date as dt_date, time as dt_time
from bson import ObjectId

class CareReminderRecord(Record):
    def __init__(self, message, daily, pet_id, time_str, date=None, _id=None, active=True):
        super().__init__(date, _id)
        self.message = message
        self.daily = daily
        self.time_str = self._format_time_str(time_str)
        self.pet_id = pet_id
        self.active = active
        self.date = datetime.fromisoformat(date) if isinstance(date, str) else date or datetime.now()
        # 不自動產生 _id，使用外部給定
        self._id = _id  
        self.db = None  # 須外部注入才能操作資料庫

    def _format_time_str(self, t):
        if isinstance(t, dt_time):
            return t.strftime("%H:%M")
        elif isinstance(t, str):
            # 嘗試 parse，保證是 HH:MM 或 HH:MM:SS 格式
            fmt = "%H:%M" if len(t) == 5 else "%H:%M:%S"
            return datetime.strptime(t, fmt).time().strftime("%H:%M")
        raise ValueError("無效的 time_str 格式")

    def view_record(self):
        return f"{self.date.date()} 照護提醒: {self.message}, 時間: {self.time_str}, 每日: {'是' if self.daily else '否'}"

    def update_record(self, **kwargs):
        if 'message' in kwargs:
            self.message = kwargs['message']
        if 'daily' in kwargs:
            self.daily = kwargs['daily']
        if 'time_str' in kwargs:
            self.time_str = self._format_time_str(kwargs['time_str'])
        if 'active' in kwargs:
            self.active = kwargs['active']

    def to_dict(self):
        d = {
            "_id": self._id if self._id else None,
            "type": "remind",
            "message": self.message,
            "daily": self.daily,
            "time_str": self.time_str,
            "pet_id": self.pet_id,
            "active": self.active,
        }
        # 移除 None 的 _id 以避免不必要欄位
        if d["_id"] is None:
            d.pop("_id")
        return d

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            message=data.get("message"),
            daily=data.get("daily"),
            time_str=data.get("time_str"),
            pet_id=data.get("pet_id"),
            _id=data.get("_id"),
            active=data.get("active", True),
            date=data.get("date")
        )