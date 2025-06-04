class EmailNotifier:
    def __init__(self, email_service, user_email,db):
        self.email_service = email_service
        self.user_email = user_email
        self.db = db

    def notify_low_stock(self, inventory):
        message = (
            f"[庫存提醒] {inventory.item_name}庫存量:{inventory.quantity} "
            f"低於警戒線:{inventory.threshold}！"
        )
        self.email_service.send_email(self.user_email, "食物庫存提醒", message)


    def remind_time_up(self, care_reminder):
        # 從 care_reminder 中取得 pet_id
        pet_id = care_reminder.pet_id if hasattr(care_reminder, "pet_id") else care_reminder.get("pet_id")

        # 查找 pet 名稱
        
        pet = self.db.users.find_one({"pets.pet_id": pet_id}, {"pets.$": 1})
        
        pet_name = pet["pets"][0]["name"] if pet and "pets" in pet and pet["pets"] else "未知寵物"

        # 組合時間字串
        if not care_reminder.daily:  # ➜ 非每日，就是單次提醒
            time_str = f"{care_reminder.date.isoformat()} {care_reminder.time_str}"
        else:
            time_str = care_reminder.time_str

        message = (
            f"[照護提醒] 寵物:{pet_name} 時間:{time_str}"
            f"          事件:{care_reminder.message}"
        )
        self.email_service.send_email(self.user_email, "照護提醒", message)