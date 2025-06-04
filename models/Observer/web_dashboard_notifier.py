from services.notification_service import NotificationService

class WebDashboardNotifier:
    def __init__(self, db, user_id):
        self.notification_service = NotificationService(db)
        self.user_id = user_id

    def notify_low_stock(self, inventory):
        message = (
            f"[庫存提醒] {inventory.item_name}庫存量:{inventory.quantity} "
            f"低於警戒線:{inventory.threshold}！"
        )
        self.notification_service.add_notification(self.user_id, message, type="LOW_STOCK")