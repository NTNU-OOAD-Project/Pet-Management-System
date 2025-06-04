from models.record.inventory_record import InventoryRecord
from bson import ObjectId
from models.inventory import Inventory  # 引入方便組裝 inv

class InventoryService:
    observers = []

    @staticmethod
    def apply_inventory_record(record: InventoryRecord, db):
        if not record.user_id:
            raise ValueError("InventoryRecord 缺少 user_id")
        user = db.users.find_one({"_id": ObjectId(record.user_id)})
        if not user:
            raise ValueError("找不到對應的使用者")

        inventory = user.get("inventory", [])
        matched = next((item for item in inventory if item["item_name"] == record.item_name), None)
        if matched:
            matched["quantity"] += int(record.delta_quantity)
            matched.setdefault("records", []).append(record.to_dict())
        else:
            matched = {
                "time_str": record.time_str,
                "item_name": record.item_name,
                "quantity": record.delta_quantity,
                "threshold": 0,
                "records": [record.to_dict()]
            }
            inventory.append(matched)

        # 寫回資料庫
        db.users.update_one(
            {"_id": ObjectId(record.user_id)},
            {"$set": {"inventory": inventory}}
        )
        # 包裝為 Inventory 物件以便傳給 observer
        inv = Inventory.from_dict(matched)
        if inv.threshold is not None and inv.quantity < inv.threshold:
            for observer in InventoryService.observers:
                observer.notify_low_stock(inv)
