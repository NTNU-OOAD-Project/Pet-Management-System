from typing import List, Dict

class FoodInventory:
    def __init__(self):
        self.inventory = {}         # food_name → current amount
        self.thresholds = {}        # food_name → threshold value
        self.observers = []         # list of LowStockObserver

    def add_observer(self, observer):
        """新增需要被通知的觀察者（如 User）"""
        self.observers.append(observer)

    def remove_observer(self, observer):
        """移除觀察者"""
        if observer in self.observers:
            self.observers.remove(observer)

    def add_food(self, name, amount):
        """補充庫存：新增或累加某種食物"""
        self.inventory[name] = self.inventory.get(name, 0) + amount
        print(f"已補充 {amount} 單位 {name}，目前存量：{self.inventory[name]}")

    def set_threshold(self, name, threshold):
        """設定某種食物的警戒門檻"""
        self.thresholds[name] = threshold
        print(f"設定 {name} 門檻為 {threshold}")

    def consume_food(self, name, amount):
        """消耗食物，並檢查是否低於門檻"""
        if name not in self.inventory:
            raise ValueError(f"尚未加入 {name} 到庫存")

        if self.inventory[name] < amount:
            raise ValueError(f"{name} 庫存不足：現有 {self.inventory[name]}，欲消耗 {amount}")

        self.inventory[name] -= amount
        print(f"消耗 {amount} 單位 {name}，剩餘：{self.inventory[name]}")
        self.check_and_notify(name)

    def sync_from_record_log(self, change_log: List[Dict]):
        for entry in change_log:
            if entry["type"] != "diet":
                continue  # 只處理飲食紀錄

            food = entry.get("food")
            amount = entry.get("amount")
            delta = entry.get("delta")

            if entry["action"] == "add":
                self.consume_food(food, amount)
            elif entry["action"] == "delete":
                self.add_food(food, amount)
            elif entry["action"] == "update":
                if delta is not None:
                    if delta > 0:
                        self.consume_food(food, delta)
                    elif delta < 0:
                        self.add_food(food, -delta)


    def check_and_notify(self, name):
        """若食物低於門檻，通知所有觀察者"""
        if name in self.thresholds and self.inventory.get(name, 0) <= self.thresholds[name]:
            for observer in self.observers:
                observer.notify_low_stock(name, self.inventory[name])

    def print_inventory(self):
        """印出所有庫存現況"""
        print("📊 當前食物庫存：")
        for name, amount in self.inventory.items():
            print(f" - {name}: {amount}")

    def to_dict(self):
        return {
            "inventory": self.inventory,
            "thresholds": self.thresholds
        }
