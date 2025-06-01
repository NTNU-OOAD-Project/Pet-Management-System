from pymongo import MongoClient
from models.record.inventory_record import InventoryRecord
from models.inventory import Inventory
from services.record_manager import RecordManager
from services.inventory_service import InventoryService

class PrintObserver:
    def notify_low_stock(self, inventory: Inventory):
        print(f"⚠️ [通知] {inventory.item_name} 庫存:{inventory.quantity} 低於警戒:{inventory.threshold}")

# 初始化 MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["test_inventory_db"]

# 初始化服務
record_manager = RecordManager()
observer = PrintObserver()
service = InventoryService(observers=[observer], record_manager=record_manager)

# 建立一筆測試庫存記錄（買入）
record = InventoryRecord(item_name="測試飼料", delta_quantity=+50, reason="買入")
record_manager.save_single_to_db(record, db)

# 呼叫應用方法
service.apply_inventory_record(record, db)

# 查詢結果
final = db.inventory.find_one({"item_name": "測試飼料"})
print(f"[MongoDB] 庫存建立成功：{final}")
