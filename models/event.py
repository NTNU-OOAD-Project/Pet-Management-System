from bson import ObjectId
from datetime import datetime

class EventManager:
    def __init__(self, db):
        self.collection = db['events']
        self.signup_collection = db['event_signups']

    def create_event(self, data):
        data['event_time'] = datetime.strptime(data['event_time'], '%Y-%m-%dT%H:%M')
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_all_events(self):
        events = list(self.collection.find())
        for e in events:
            e['_id'] = str(e['_id'])
        return events
    
    def get_all_events_by_category(self, category):
        events = list(self.collection.find({"category": category}))
        for e in events:
            e['_id'] = str(e['_id'])
        return events

    def get_event_by_id(self, event_id):
        return self.collection.find_one({'_id': ObjectId(event_id)})

    def signup_event(self, user_id, event_id):
        exists = self.signup_collection.find_one({
            "user_id": user_id,
            "event_id": event_id
        })
        if exists:
            return False
        self.signup_collection.insert_one({
            "user_id": user_id,
            "event_id": event_id
        })
        return True
    
    def cancel_signup(self, user_id, event_id):
        result = self.signup_collection.delete_one({
            "user_id": user_id,
            "event_id": event_id
        })
        return result.deleted_count > 0

    def get_user_signed_events(self, user_id):
        signups = list(self.signup_collection.find({"user_id": user_id}))
        event_ids = [ObjectId(s['event_id']) for s in signups]
        events = list(self.collection.find({"_id": {"$in": event_ids}}))
        for e in events:
            e['_id'] = str(e['_id'])
        return events
