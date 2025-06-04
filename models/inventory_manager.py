from bson import ObjectId
import uuid

class InventoryManager:
    def __init__(self, db):
        self.db = db

    def get_inventory_list(self, user_id):
        user = self.db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("找不到使用者")
        inventory = user.get("inventory", [])
        # 將 ObjectId 轉字串方便使用
        for item in inventory:
            if "_id" in item and not isinstance(item["_id"], str):
                item["_id"] = str(item["_id"])
        return inventory

    def add_inventory(self, user_id, item_name, quantity, threshold):
        # 產生唯一id(非 ObjectId)
        new_id = str(uuid.uuid4())
        new_inventory = {
            "_id": new_id,
            "item_name": item_name,
            "quantity": int(quantity),
            "threshold": int(threshold)
        }
        result = self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$push": {"inventory": new_inventory}}
        )
        if result.modified_count == 0:
            raise Exception("新增失敗")
        return new_id

    def update_inventory(self, user_id, inventory_id, item_name, quantity, threshold):
        result = self.db.users.update_one(
            {
                "_id": ObjectId(user_id),
                "inventory._id": inventory_id
            },
            {
                "$set": {
                    "inventory.$.item_name": item_name,
                    "inventory.$.quantity": int(quantity),
                    "inventory.$.threshold": int(threshold)
                }
            }
        )
        if result.modified_count == 0:
            raise Exception("更新失敗，找不到該項目")

    def delete_inventory(self, user_id, inventory_id):
        result = self.db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$pull": {"inventory": {"_id": inventory_id}}}
        )
        if result.modified_count == 0:
            raise Exception("刪除失敗，找不到該項目")
    
    def get_low_stock_items(self, user_id):
        """回傳用戶所有低於或等於警戒值的存貨列表"""
        inventory = self.get_inventory_list(user_id)
        low_stock = [item for item in inventory if item["quantity"] <= item["threshold"]]
        return low_stock

    def get_low_stock_count(self, user_id):
        """回傳低庫存項目數"""
        return len(self.get_low_stock_items(user_id))