from services.notification_service import NotificationService
from services.email_service import send_email


class CareReminder:
    def __init__(self, message, time, date, type):
        self.message = message
        self.time = time
        self.date = date
        self.type = type

    def is_due_now(self, current_time):
        from datetime import datetime
        if self.type == "DAILY":
            return current_time.time() >= self.time
        elif self.type == "ONE_TIME":
            return current_time.date() == self.date and current_time.time() >= self.time
        return False

    def remind(self, owner, pet, db):
        message = f'[照護提醒] <strong>寵物：</strong>{pet.name}　　<strong>代辦事項：</strong>{self.message}'
        ns = NotificationService(db)
        ns.add_notification(user_id=owner.user_id, message=message, type="CARE_REMINDER")