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

    def view_record(self):
        return f"{self.date} 健康狀況: {self.details}, 疫苗: {self.vaccine}"

    def update_record(self, details=None, vaccine=None):
        if details:
            self.details = details
        if vaccine:
            self.vaccine = vaccine

    def to_dict(self):
        return {
            "_id": self._id if self._id else ObjectId(),
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
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            species=data.get("species"),
            name=data.get("name"),
            age=data.get("age"),
            details=data.get("details"),
            vaccine=data.get("vaccine"),
            medications=data.get("medications", []),
            pet_id=data.get("pet_id"),
            date=datetime.fromisoformat(data["date"]) if "date" in data else None,
            _id=data.get("_id")
        )