class EmailNotifier:
    def __init__(self, email_service, user_email):
        self.email_service = email_service
        self.user_email = user_email

    def notify_low_stock(self, inventory):
        message = (
            f"[庫存提醒] {inventory.item_name}庫存量:{inventory.quantity} "
            f"低於警戒線:{inventory.threshold}！"
        )
        self.email_service.send_email(self.user_email, "食物庫存提醒", message)
