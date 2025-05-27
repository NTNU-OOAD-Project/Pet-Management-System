# user.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

class User:
    def __init__(self, db):
        self.db = db
        self.collection = db['users']

    def register(self, name, email, phone, password):
        # 檢查是否有重複 email
        if self.collection.find_one({"email": email}):
            return False, "Email 已被註冊"
        hashed_pw = generate_password_hash(password)
        user = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": hashed_pw,
            "pets": []
        }
        result = self.collection.insert_one(user)
        return True, str(result.inserted_id)

    def login(self, email, password):
        user = self.collection.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            session['user_id'] = str(user['_id'])
            session['user_name'] = user['name']
            return True, "登入成功"
        else:
            return False, "帳號或密碼錯誤"

    def logout(self):
        session.clear()

    def get_current_user(self):
        if 'user_id' in session:
            user = self.collection.find_one({"_id": self._str_to_objectid(session['user_id'])})
            if user:
                user['_id'] = str(user['_id'])
                return user
        return None

    def get_user_by_email(self, email):
        user = self.collection.find_one({'email': email})
        return user
    