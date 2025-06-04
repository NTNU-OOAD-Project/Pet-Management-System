from models.record.base import Record
from datetime import datetime
from bson import ObjectId

class HealthRecord(Record):
    def __init__(self, species, name, age, details, vaccine, medications=None, pet_id=None, date=None, _id=None):
        super().__init__(date, _id)
        self.species = species
        self.name = name
        self.age = age
        self.details = details
        self.vaccine = vaccine
        self.medications = medications or []
        self.pet_id = pet_id
        self._id = _id  
        self.db = None  # 外部注入

    def view_record(self):
        return f"{self.date.date()} 健康狀況: {self.details}, 疫苗: {self.vaccine}"

    def update_record(self, **kwargs):
        if 'species' in kwargs:
            self.species = kwargs['species']
        if 'name' in kwargs:
            self.name = kwargs['name']
        if 'age' in kwargs:
            self.age = kwargs['age']
        if 'details' in kwargs:
            self.details = kwargs['details']
        if 'vaccine' in kwargs:
            self.vaccine = kwargs['vaccine']
        if 'medications' in kwargs:
            self.medications = kwargs['medications']
        if 'date' in kwargs:
            d = kwargs['date']
            self.date = datetime.fromisoformat(d) if isinstance(d, str) else d

    def to_dict(self):
        d = {
            "type": "health",
            "date": self.date.isoformat(),
            "species": self.species,
            "name": self.name,
            "age": self.age,
            "details": self.details,
            "vaccine": self.vaccine,
            "medications": self.medications,
            "pet_id": self.pet_id
        }
        if self._id:
            d["_id"] = self._id
        return d

    @classmethod
    def from_dict(cls, data: dict):
        _id = data.get("_id")
        if _id and not isinstance(_id, str):
            _id = str(_id)

        return cls(
            species=data.get("species"),
            name=data.get("name"),
            age=data.get("age"),
            details=data.get("details"),
            vaccine=data.get("vaccine"),
            medications=data.get("medications", []),
            pet_id=data.get("pet_id"),
            date=datetime.fromisoformat(data["date"]) if "date" in data else None,
            _id=_id
        )

    def add_health_record(self, species, name, age, details, vaccine, medications, pet_id, date=None):
        if self.db is None:
            raise RuntimeError("請先設定 db 屬性")

        new_record = {
            "species": species,
            "name": name,
            "age": age,
            "details": details,
            "vaccine": vaccine,
            "medications": medications,
            "pet_id": pet_id,
            "date": date,
            "_id": str(ObjectId())  # 可考慮改成不產生，依需求
        }

        result = self.db.users.update_one(
            {"pets.pet_id": pet_id},
            {"$push": {"pets.$.health_records": new_record}}
        )

        if result.modified_count == 0:
            raise ValueError(f"找不到 pet_id={pet_id} 或無法新增健康紀錄")

        return new_record