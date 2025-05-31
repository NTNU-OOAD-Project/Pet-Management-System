from typing import List, Dict
from models.record.base import Record
from models.record.diet_record import DietRecord
from models.record.health_record import HealthRecord

class RecordManager:
    def __init__(self):
        self._records: List[Record] = []
        self._change_log: List[Dict] = []

    def add_record(self, record: Record):
        self._records.append(record)
        self._change_log.append({
            "action": "add",
            "type": record.to_dict().get("type"),
            "food": getattr(record, "food_name", None),
            "amount": getattr(record, "amount", None),
            "record_id": record.id
        })

    def create_record(self, type_str: str, **kwargs) -> Record:
        record_cls = self._get_record_class(type_str)
        return record_cls(**kwargs)

    def add_record_by_type(self, type_str: str, **kwargs):
        record = self.create_record(type_str, **kwargs)
        self.add_record(record)

    def delete_record_by_id(self, record_id: int) -> bool:
        for i, r in enumerate(self._records):
            if r.id == record_id:
                self._change_log.append({
                    "action": "delete",
                    "type": r.to_dict().get("type"),
                    "food": getattr(r, "food_name", None),
                    "amount": getattr(r, "amount", None),
                    "record_id": r.id
                })
                del self._records[i]
                return True
        return False

    def update_record_by_id(self, record_id: int, **kwargs) -> bool:
        for r in self._records:
            if r.id == record_id:
                old_amount = getattr(r, "amount", None)
                r.update_record(**kwargs)
                new_amount = getattr(r, "amount", None)
                self._change_log.append({
                    "action": "update",
                    "type": r.to_dict().get("type"),
                    "food": getattr(r, "food_name", None),
                    "amount": new_amount,
                    "delta": (new_amount - old_amount) if old_amount is not None and new_amount is not None else None,
                    "record_id": r.id
                })
                return True
        return False

    def view_all(self):
        return [r.to_dict() for r in self._records]

    def view_by_type(self, type_str: str):
        return [r.to_dict() for r in self._records if r.to_dict().get("type") == type_str]

    def to_list(self):
        return self.view_all()

    def get_change_log(self) -> List[Dict]:
        return self._change_log.copy()

    def clear_change_log(self):
        self._change_log.clear()

    def _get_record_class(self, type_str: str):
        record_types = {
            "diet": DietRecord,
            "health": HealthRecord
        }
        record_cls = record_types.get(type_str)
        if not record_cls:
            raise ValueError(f"Unknown record type: {type_str}")
        return record_cls
