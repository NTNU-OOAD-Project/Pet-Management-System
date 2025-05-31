#In[0]  Initialization 
from flask import Flask, render_template, session, jsonify, request, flash, redirect, url_for
from flask_cors import CORS  # aichat only
from pymongo import MongoClient
from models.place import PlaceMap
from dotenv import load_dotenv
from datetime import datetime, timezone
import os

from models.user import User
from models.services.notification_service import NotificationService
from models.food_inventory import InventoryManager

app = Flask(__name__)
CORS(app)  
app.secret_key = 'your_secret_key'

load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

messages_collection = db["messages"]  # aichat
inventory_manager = InventoryManager(db)  # kaitai

# == [首頁] ==
@app.route('/')
def index():
    return render_template('index.html')

#In[1] Notification: kaitai only
@app.context_processor
def inject_unread_notification_count():
    user_service = User(db)
    current_user = user_service.get_current_user() if hasattr(user_service, 'get_current_user') else None

    if current_user:
        notif_service = NotificationService(db)
        unread_count = notif_service.get_unread_count(current_user['_id'])
    else:
        unread_count = 0
    return dict(unread_count=unread_count)



#In[2] User Management]

# 登入頁面
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# 登入
@app.route('/login', methods=['POST'])
def login():
    user = User(db)
    email = request.form.get('email')
    password = request.form.get('password')
    success, msg = user.login(email, password)
    if success:
        # aichat: 存 session, kaitai: 只 flash
        user_info = user.get_user_by_email(email) if hasattr(user, 'get_user_by_email') else None
        if user_info:
            session['user_id'] = str(user_info['_id'])
            session['user_name'] = user_info['name']
        flash('登入成功', 'success')
        return redirect(url_for('index'))
    else:
        flash(msg, 'danger')
        # aichat: 回登入頁；kaitai: 回首頁
        return redirect(url_for('login_page'))

# 登出（aichat 會 pop user_name, kaitai 沒有）
@app.route('/logout')
def logout():
    user = User(db)
    user.logout()
    session.pop('user_name', None)  # aichat only
    flash('已登出', 'info')
    return redirect(url_for('index'))

# 註冊頁面（aichat only）
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# 註冊處理（以 aichat 版本為主）
@app.route('/register', methods=['POST'])
def register():
    user = User(db)
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    password = request.form.get('password')
    success, msg = user.register(name, email, phone, password)
    if success:
        flash('註冊成功，請登入', 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('login_page'))  # aichat 會回登入頁

#In[3] Place
@app.route('/place')
def place_view():
    place_map = PlaceMap(db)
    place_html = place_map.generate_map_html()
    is_logged_in = 'user_id' in session
    return render_template('place.html', map_html=place_html, is_logged_in=is_logged_in)

@app.route('/place/detail/<place_id>')
def place_detail(place_id):
    place_map = PlaceMap(db)
    place = place_map.get_place_detail(place_id)
    if place:
        place['_id'] = str(place['_id'])
        return jsonify({"status": "success", "data": place})
    return jsonify({"status": "fail", "msg": "Place not found"})

@app.route('/place/reserve', methods=['POST'])
def place_reserve():
    if 'user_id' not in session:
        return jsonify({'status': 'fail', 'msg': '請先登入'})
    place_id = request.json.get('place_id')
    reserve_info = request.json.get('reserve_info')
    user_id = session['user_id']
    place_map = PlaceMap(db)
    place_map.reserve_spot(place_id, user_id, reserve_info)
    return jsonify({'status': 'success', 'msg': '預約成功！'})

#In[4] 寵物管理
@app.route('/pets')
def pets():    
    return render_template('mypet.html')

@app.route('/health')
def health():
    return render_template('health.html')

@app.route('/diet')
def diet():
    return render_template('diet.html')

@app.route('/reminder')
def reminder():
    return render_template('reminder.html')

#In[5] 醫療服務
from models.medical_service import MedicalService

@app.route('/medical', methods=['GET', 'POST'])
def medical():
    service = MedicalService(db)
    if request.method == 'POST':
        if 'user_id' not in session:
            flash("請先登入才能預約", "warning")
            return redirect(url_for('index'))

        service_type = request.form.get('service_type')
        vet_name = request.form.get('vet_name')
        clinic_name = request.form.get('clinic_name')
        appointment_str = request.form.get('appointment_time')
        appointment_time = datetime.strptime(appointment_str, "%Y-%m-%dT%H:%M")
        service_location = request.form.get('service_location')

        service.schedule_service(
            session['user_id'], service_type, vet_name, clinic_name,
            appointment_time, service_location
        )
        flash("預約成功", "success")
        return redirect(url_for('medical'))

    if 'user_id' in session:
        user_id = session['user_id']

        filters = {
            "service_type": request.args.get("service_type"),
            "clinic_name": request.args.get("clinic_name"),
            "appointment_date": request.args.get("appointment_date")
        }
        filters = {k: v for k, v in filters.items() if v}

        services = service.list_user_services(user_id, filters)

        for s in services:
            s['_id'] = str(s['_id'])
    else:
        services = []

    return render_template('medical.html', services=services)

@app.route('/medical/cancel/<service_id>', methods=['POST'])
def cancel_medical(service_id):
    if 'user_id' not in session:
        flash("請先登入", "warning")
        return redirect(url_for('index'))

    service = MedicalService(db)
    success = service.cancel_service_by_id(service_id, session['user_id'])
    if success:
        flash("預約已成功取消", "success")
    else:
        flash("取消失敗，請稍後再試", "danger")
    return redirect(url_for('medical'))

@app.route('/medical/edit/<service_id>', methods=['POST'])
def edit_medical(service_id):
    if 'user_id' not in session:
        flash("請先登入", "warning")
        return redirect(url_for('index'))

    service_type = request.form.get('service_type')
    vet_name = request.form.get('vet_name')
    clinic_name = request.form.get('clinic_name')
    appointment_str = request.form.get('appointment_time')
    appointment_time = datetime.strptime(appointment_str, "%Y-%m-%dT%H:%M")
    service_location = request.form.get('service_location')

    service = MedicalService(db)
    service.update_service_by_id(
        service_id, session['user_id'],
        service_type, vet_name, clinic_name,
        appointment_time, service_location
    )

    flash("預約已更新", "success")
    return redirect(url_for('medical'))


#In[5] supplies
'''
@app.route('/supplies')
def supplies():
    return render_template('supplies.html')
'''

#In[6] 活動預約
@app.route('/event')
def event():
    return render_template('event.html')

#In[7] AI 智能助理 (aichat only)
@app.route("/api/messages", methods=["POST"])
def save_message():
    if 'user_id' not in session:
        return jsonify({"error": "尚未登入"}), 401

    data = request.json
    required_fields = ("conversationId", "sender", "content", "timestamp")
    if not data or not all(k in data for k in required_fields):
        return jsonify({"error": "資料格式錯誤"}), 400

    try:
        utc_now = datetime.now(timezone.utc)
        local_date = utc_now.strftime("%Y-%m-%d")
        time_str = data["timestamp"]
        datetime_str = f"{local_date} {time_str}"
    except Exception as e:
        return jsonify({"error": f"時間處理錯誤: {str(e)}"}), 400

    message_doc = {
        "conversationId": data["conversationId"],
        "sender": data["sender"],
        "content": data["content"],
        "datetime": datetime_str,
        "user_id": session["user_id"],
        "title": data.get("title", "")
    }

    try:
        result = messages_collection.insert_one(message_doc)
        return jsonify({
            "success": True,
            "inserted_id": str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/messages", methods=["GET"])
def get_message():
    if 'user_id' not in session:
        return jsonify({"error": "尚未登入"}), 401

    user_id = session["user_id"]
    try:
        messages = list(messages_collection.find({"user_id": user_id}))
        for msg in messages:
            msg["_id"] = str(msg["_id"])
        return jsonify({"success": True, "messages": messages})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#In[5]  Food Inventory
@app.route('/user/<user_id>/add_food', methods=['POST'])
def add_food(user_id):
    data = request.get_json()
    name = data.get("name")
    amount = float(data.get("amount", 0))
    success, msg = inventory_manager.add_food(user_id, name, amount)
    return jsonify({'status': 'success' if success else 'fail', 'msg': msg})

@app.route('/user/<user_id>/consume_food', methods=['POST'])
def consume_food(user_id):
    data = request.get_json()
    name = data.get("name")
    amount = float(data.get("amount", 0))
    success, msg = inventory_manager.consume_food(user_id, name, amount)
    return jsonify({'status': 'success' if success else 'fail', 'msg': msg})

# == [Main function] ==
if __name__ == '__main__':
    app.run(debug=True)
