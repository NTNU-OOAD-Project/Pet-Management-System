from bson.objectid import ObjectId
from datetime import datetime, timedelta

class MedicalService:
    def __init__(self, db):
        self.collection = db["medical_services"]

    def schedule_service(self, user_id, service_type, vet_name, clinic_name, appointment_time, service_location):
        new_service = {
            "user_id": user_id,
            "service_type": service_type,
            "vet_name": vet_name,
            "clinic_name": clinic_name,
            "appointment_time": appointment_time,
            "service_location": service_location
        }
        result = self.collection.insert_one(new_service)
        return str(result.inserted_id)

    def list_user_services(self, user_id, filters=None):
        query = {"user_id": user_id}
        
        if filters:
            if "service_type" in filters and filters["service_type"]:
                query["service_type"] = filters["service_type"]

            if "clinic_name" in filters and filters["clinic_name"]:
                query["clinic_name"] = {
                    "$regex": filters["clinic_name"],
                    "$options": "i"
                }

            if "appointment_date" in filters and filters["appointment_date"]:
                try:
                    date_start = datetime.strptime(filters["appointment_date"], "%Y-%m-%d")
                    date_end = date_start + timedelta(days=1)
                    query["appointment_time"] = {
                        "$gte": date_start,
                        "$lt": date_end
                    }
                except Exception as e:
                    print("日期轉換錯誤:", e)

        return list(self.collection.find(query))

    def view_service_detail(self, service_id, user_id=None):
        query = {"_id": ObjectId(service_id)}
        if user_id:
            query["user_id"] = user_id
        return self.collection.find_one(query)

    def cancel_service_by_id(self, service_id, user_id):
        return self.collection.delete_one({
            "_id": ObjectId(service_id),
            "user_id": user_id
        }).deleted_count > 0
    
    def update_service_by_id(self, service_id, user_id, service_type, vet_name, clinic_name, appointment_time, service_location):
        result = self.collection.update_one(
            {"_id": ObjectId(service_id), "user_id": user_id},
            {"$set": {
                "service_type": service_type,
                "vet_name": vet_name,
                "clinic_name": clinic_name,
                "appointment_time": appointment_time,
                "service_location": service_location
            }}
        )
        return result.modified_count > 0
