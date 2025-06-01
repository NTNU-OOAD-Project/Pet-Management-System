from bson.objectid import ObjectId

class PetManager:
    def __init__(self, db):
        self.db = db
        self.users = db['users']

    def get_pets_of_user(self, user_id):
        user = self.users.find_one({'_id': ObjectId(user_id)})
        if user and 'pets' in user:
            return user['pets']
        return []


    def add_pet(self, user_id, data):
        # 必要欄位
        name = data.get('name')
        species = data.get('species')
        age = data.get('age')
        health_status = data.get('health_status')
        if not all([name, species, age, health_status]):
            return False, None, "欄位不得為空"

        try:
            pet_data = {
                'pet_id': str(ObjectId()),
                'name': name,
                'species': species,
                'age': int(age),
                'health_status': health_status,
                'diet_records': [],
                'exercise_records': [],
                'health_records': [],
                'care_schedule': {}
            }
            self.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$push': {'pets': pet_data}}
            )
            return True, pet_data['pet_id'], ""
        except Exception as e:
            return False, None, str(e)

    def remove_pet(self, user_id, pet_id):
        self.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$pull': {'pets': {'pet_id': pet_id}}}
        )

    def update_pet(self, user_id, pet_id, update_data):
        result = self.users.update_one(
            {'_id': ObjectId(user_id), 'pets.pet_id': pet_id},
            {'$set': {f'pets.$.{k}': v for k, v in update_data.items()}}
        )
        return result.modified_count > 0
