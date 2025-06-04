from models.record.remind_record import CareReminderRecord
from datetime import datetime

class RemindService:
    observers = []

    @staticmethod
    def add_observer(observer):
        RemindService.observers.append(observer)

    @staticmethod
    def check_and_notify(reminder: CareReminderRecord):
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")

        if reminder.daily:
            if reminder.time_str == current_time_str:
                RemindService._notify_all(reminder)
                # DAILY 不改變 active

        else:
            if reminder.active and reminder.time_str == current_time_str:
                RemindService._notify_all(reminder)
                reminder.active = False  # 檢查完就停用

    @staticmethod
    def _notify_all(reminder: CareReminderRecord):
        for observer in RemindService.observers:
            observer.remind_time_up(reminder)