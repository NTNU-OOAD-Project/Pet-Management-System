from services.notification_service import NotificationService

class WebDashboardNotifier:
    def __init__(self, db, user_id):
        self.notification_service = NotificationService(db)
        self.user_id = user_id

    def notifyLowStock(self, food, amount):
        message = f"[庫存提醒] {food} 庫存過低，目前僅剩 {amount}。"
        self.notification_service.add_notification(self.user_id, message, type="LOW_STOCK")
