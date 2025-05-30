class EmailNotifier:
    def __init__(self, email_service, user_email):
        self.email_service = email_service
        self.user_email = user_email

    def notifyLowStock(self, food, amount):
        message = f"[庫存提醒] 您的 {food} 庫存不足，目前僅剩 {amount} 單位。"
        self.email_service.send_email(self.user_email, "食物庫存提醒", message)
