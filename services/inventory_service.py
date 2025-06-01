from models.inventory import Inventory
from models.record.inventory_record import InventoryRecord

class InventoryService:
    def __init__(self, observers=None, record_manager=None):
        self.observers = observers or []
        self.record_manager = record_manager


    def apply_inventory_record(self, record: InventoryRecord, db):
        inventory_data = db.inventory.find_one({"item_name": record.item_name})
        if inventory_data:
            inv = Inventory.from_dict(inventory_data)
        else:
            inv = Inventory(item_name=record.item_name, quantity=0)

        inv.quantity += record.delta_quantity

        db.inventory.update_one(
            {"item_name": inv.item_name},
            {"$set": inv.to_dict()},
            upsert=True
        )

        # ✅ 加上庫存警戒線檢查與通知
        if inv.threshold is not None and inv.quantity < inv.threshold:
            for observer in self.observers:
                observer.notify_low_stock(inv)
