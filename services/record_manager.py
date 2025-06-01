from typing import Dict
from bson import ObjectId
from models.record.diet_record import DietRecord
from models.record.health_record import HealthRecord
from models.record.inventory_record import InventoryRecord
from models.record.base import Record
from services.inventory_service import InventoryService

class RecordManager:
    def save_single_to_db(self, record: Record, db):
        record_type = record.to_dict().get("type")
        collection = db[f"{record_type}_records"]
        collection.insert_one(record.to_dict())

    def add_record(self, record: Record, db):
        self.save_single_to_db(record, db)

        if record.to_dict().get("type") == "diet":
            inv_record = InventoryRecord(
                item_name=record.food_name,
                delta_quantity=-record.amount,
                reason="食用"
            )
            self.save_single_to_db(inv_record, db)
            InventoryService().apply_inventory_record(inv_record, db)

    def update_record(self, record_id: ObjectId, type_str: str, update_fields: Dict, db):
        collection = db[f"{type_str}_records"]

        if type_str == "diet":
            old_record = collection.find_one({"_id": ObjectId(record_id)})
            if not old_record:
                raise ValueError("找不到原始 diet 記錄")

            old_food = old_record["food_name"]
            old_amount = old_record["amount"]

            new_food = update_fields.get("food_name", old_food)
            new_amount = update_fields.get("amount", old_amount)

            if old_food == new_food:
                delta = old_amount - new_amount
                if delta != 0:
                    inv_record = InventoryRecord(old_food, delta, "diet 修改")
                    self.save_single_to_db(inv_record, db)
                    InventoryService().apply_inventory_record(inv_record, db)
            else:
                self.save_single_to_db(InventoryRecord(old_food, old_amount, "diet 修改退回"), db)
                InventoryService().apply_inventory_record(
                    InventoryRecord(old_food, old_amount, "diet 修改退回"), db
                )
                self.save_single_to_db(InventoryRecord(new_food, -new_amount, "diet 修改扣除"), db)
                InventoryService().apply_inventory_record(
                    InventoryRecord(new_food, -new_amount, "diet 修改扣除"), db
                )

        collection.update_one({"_id": ObjectId(record_id)}, {"$set": update_fields})

    def delete_record(self, record_id: ObjectId, type_str: str, db):
        collection = db[f"{type_str}_records"]

        if type_str == "diet":
            record = collection.find_one({"_id": ObjectId(record_id)})
            if record:
                inv_record = InventoryRecord(record["food_name"], record["amount"], "diet 刪除補回")
                self.save_single_to_db(inv_record, db)
                InventoryService().apply_inventory_record(inv_record, db)

        collection.delete_one({"_id": ObjectId(record_id)})

    def view_all(self, type_str: str, db):
        collection = db[f"{type_str}_records"]
        return list(collection.find())

    def _get_record_class(self, type_str: str):
        record_types = {
            "diet": DietRecord,
            "health": HealthRecord,
            "inventory": InventoryRecord
        }
        return record_types.get(type_str)
