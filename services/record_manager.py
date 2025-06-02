from typing import Dict
from bson import ObjectId
from models.record.diet_record import DietRecord
from models.record.health_record import HealthRecord
from models.record.inventory_record import InventoryRecord
from models.record.base import Record
from services.inventory_service import InventoryService

class RecordManager:
    def add_record_by_type(self, type_str: str, data: Dict, db) -> Record:
        record_class = self._get_record_class(type_str)
        if not record_class:
            raise ValueError(f"不支援的紀錄類型：{type_str}")

        try:
            record = record_class.from_dict(data)
            self.add_record(record, db)
            return record
        except Exception as e:
            raise ValueError(f"建立紀錄失敗：{str(e)}")

    def save_single_to_db(self, record: Record, db):
        record_dict = record.to_dict()
        record_type = record_dict.get("type")

        if record_type in ["diet", "health"]:
            pet_id = record_dict.get("pet_id")
            if not pet_id:
                raise ValueError("紀錄中缺少 pet_id，無法儲存到指定寵物下")
            field_map = {
                "diet": "diet_records",
                "health": "health_records"
            }
            field = field_map.get(record_type)
            db.users.update_one(
                {"pets.pet_id": pet_id},
                {"$push": {f"pets.$.{field}": record_dict}}
            )
        elif record.to_dict().get("type") == "inventory":
            InventoryService.apply_inventory_record(record, db)


    #新增紀錄
    def add_record(self, record: Record, db):
        self.save_single_to_db(record, db)

        if record.to_dict().get("type") == "diet":
            # 從 pet_id 查找對應 user_id
            pet_id = record.pet_id
            user = db.users.find_one({"pets.pet_id": pet_id}, {"_id": 1})
            if not user:
                raise ValueError(f"找不到對應 pet_id={pet_id} 的使用者")
            user_id = str(user["_id"])

            # 建立庫存紀錄
            inv_record = InventoryRecord(
                item_name=record.food_name,
                delta_quantity=-record.amount,
                reason="食用",
                user_id=user_id
            )
            self.add_record(inv_record, db)

    #編輯紀錄
    def update_record(self, record_id: ObjectId, type_str: str, update_fields: Dict, db):
        record_data = self.find_record_by_id(record_id, type_str, db)
        if not record_data:
            raise ValueError(f"找不到 ID 為 {record_id} 的 {type_str} 紀錄")

        record, user_id, parent_id = record_data  # parent_id 是 pet_id 或 item_name

        # 刪除原紀錄（處理庫存反向）
        self.delete_record(record_id, type_str, db)

        # 更新資料合併
        updated_data = {**record, **update_fields}
        updated_data.pop("_id", None)

        # 建立新紀錄物件並新增
        record_class = self._get_record_class(type_str)
        updated_record = record_class.from_dict(updated_data)
        self.add_record(updated_record, db)



    #刪除紀錄
    def delete_record(self, record_id: ObjectId, type_str: str, db):
        record_data = self.find_record_by_id(record_id, type_str, db)
        if not record_data:
            raise ValueError(f"找不到 ID 為 {record_id} 的 {type_str} 紀錄")

        record, user_id, parent_id = record_data  # parent_id 是 pet_id 或 item_name
        from bson import ObjectId

        if type_str == "diet":
            # 補回食物
            inv_record = InventoryRecord(
                item_name=record["food_name"],
                delta_quantity=record["amount"],
                reason="diet 刪除補回",
                user_id=user_id
            )
            self.add_record(inv_record, db)

            # 從該寵物的 diet_records 中刪除
            db.users.update_one(
                {"_id": ObjectId(user_id), "pets.pet_id": parent_id},
                {"$pull": {"pets.$.diet_records": {"_id": ObjectId(record_id)}}}
            )

        elif type_str == "health":
            db.users.update_one(
                {"_id": ObjectId(user_id), "pets.pet_id": parent_id},
                {"$pull": {"pets.$.health_records": {"_id": ObjectId(record_id)}}}
            )

        elif type_str == "inventory":
            # 套用反向庫存變動
            reverse_record = InventoryRecord.from_dict({
                **record,
                "delta_quantity": -record["delta_quantity"],
                "user_id": user_id
            })
            InventoryService.apply_inventory_record(reverse_record, db)

            # 從 inventory 中刪除該紀錄
            db.users.update_one(
                {"_id": ObjectId(user_id), "inventory.item_name": parent_id},
                {"$pull": {"inventory.$.records": {"_id": ObjectId(record_id)}}}
            )

        else:
            raise ValueError(f"尚未支援類型：{type_str}")


    #(從id、type >> 單筆資料)
    def find_record_by_id(self, record_id: str, type_str: str, db):
        obj_id = ObjectId(record_id)

        if type_str in ["diet", "health"]:
            user = db.users.find_one({f"pets.{type_str}_records._id": obj_id})
            if not user:
                return None

            for pet in user["pets"]:
                for record in pet.get(f"{type_str}_records", []):
                    if record["_id"] == obj_id:
                        return record, str(user["_id"]), pet["pet_id"]

        elif type_str == "inventory":
            user = db.users.find_one({"inventory.records._id": obj_id})
            if not user:
                return None

            for item in user["inventory"]:
                for record in item.get("records", []):
                    if record["_id"] == obj_id:
                        return record, str(user["_id"]), item["_id"]

        return None

    #(從id(pet_id、inventory_id)、type >> 所有資料)
    def view_by_type(self, db, id: str, type_str: str, user_id: str):
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("找不到使用者")

        if type_str == "inventory":
            for item in user.get("inventory", []):
                if str(item.get("_id")) == id:  # 用 item 的 _id 做比對
                    # 加上 item 名稱給每筆 record
                    for record in item.get("records", []):
                        record["item_name"] = item["item_name"]
                    return item.get("records", [])
            raise ValueError("找不到該項目的 inventory")

        elif type_str in ["diet", "health"]:
            for pet in user.get("pets", []):
                if pet["pet_id"] == id:
                    return pet.get(f"{type_str}_records", [])

            raise ValueError("找不到該寵物")

        else:
            raise ValueError(f"不支援的紀錄類型：{type_str}")



    def _get_record_class(self, type_str: str):
        record_types = {
            "diet": DietRecord,
            "health": HealthRecord,
            "inventory": InventoryRecord
        }
        return record_types.get(type_str)
