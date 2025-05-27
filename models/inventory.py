class InventoryManager:
    def __init__(self, db):
        self.users = db["users"]

    def add_food(self, user_id, name, amount):
        user = self.users.find_one({"_id": user_id})
        if not user:
            return False, "使用者不存在"

        inventory = user.get("inventory", {}).get("inventory", {})
        inventory[name] = inventory.get(name, 0) + amount

        self.users.update_one({"_id": user_id}, {"$set": {"inventory.inventory": inventory}})
        return True, f"已新增 {amount} 單位的 {name}"

    def consume_food(self, user_id, name, amount):
        user = self.users.find_one({"_id": user_id})
        if not user:
            return False, "使用者不存在"

        inventory = user.get("inventory", {}).get("inventory", {})
        thresholds = user.get("inventory", {}).get("thresholds", {})

        if name not in inventory:
            return False, f"{name} 不在庫存中"

        inventory[name] -= amount
        message = f"已消耗 {amount} 單位的 {name}"

        if inventory[name] <= thresholds.get(name, 0):
            message += f" ⚠️ 警告：{name} 庫存已低於門檻"

        self.users.update_one({"_id": user_id}, {"$set": {"inventory.inventory": inventory}})
        return True, message
