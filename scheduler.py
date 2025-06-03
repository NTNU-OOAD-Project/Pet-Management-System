from apscheduler.schedulers.background import BackgroundScheduler
from models.record.remind_record import CareReminderRecord
from services.remind_service import RemindService
from models.observer.email_notifier import EmailNotifier
from models.observer.web_dashboard_notifier import WebDashboardNotifier
from pymongo import MongoClient
from services.email_service import EmailService
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("MONGODB_DB")]

# 初始化 scheduler
scheduler = BackgroundScheduler()
# 初始化 email_service
email_service = EmailService()

# === 任務: 照護提醒 ===
def check_all_reminders():
    users = db.users.find({})
    for user in users:
        user_id = str(user["_id"])
        user_email = user.get("email", "")
        email_notifier = EmailNotifier(email_service, user_email)
        web_notifier = WebDashboardNotifier(db, user_id)

        for pet in user.get("pets", []):
            updated = False
            for i, care_remind in enumerate(pet.get("care_remind_records", [])):
                reminder = CareReminderRecord.from_dict(care_remind)
                old_active = reminder.active
                if not old_active:
                    continue

                # 加入 observer
                RemindService.observers = [email_notifier, web_notifier]
                RemindService.check_and_notify(reminder)

                # 若 active 狀態變了就更新回資料庫
                if reminder.active != old_active:
                    pet["care_remind_records"][i]["active"] = reminder.active
                    updated = True

            if updated:
                db.users.update_one(
                    {"_id": user["_id"], "pets.pet_id": pet["pet_id"]},
                    {"$set": {"pets.$.care_remind_records": pet["care_remind_records"]}}
                )

# 加入排程任務
scheduler.add_job(check_all_reminders, 'interval', minutes=1)

scheduler.start()