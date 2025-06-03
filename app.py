#In[0] Initialization
from flask import Flask, render_template, session, jsonify, request, flash, redirect, url_for
from flask_cors import CORS
from pymongo import MongoClient
from models.place import PlaceMap
from dotenv import load_dotenv
from datetime import datetime, timezone
import os

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'

#.env file
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

messages_collection = db["messages"]

@app.route('/')
def index():
    return render_template('index.html')

#In[1] User Management
from models.user import User

# 登入頁面
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# 登入處理
@app.route('/login', methods=['POST'])
def login():
    user = User(db)
    email = request.form.get('email')
    password = request.form.get('password')
    success, msg = user.login(email, password)
    if success:
        user_info = user.get_user_by_email(email)
        session['user_id'] = str(user_info['_id'])
        session['user_name'] = user_info['name']
        flash('登入成功', 'success')
        return redirect(url_for('index'))
    else:
        flash(msg, 'danger')
        return redirect(url_for('login_page'))  # 登入失敗也回 login 頁

# 登出
@app.route('/logout')
def logout():
    user = User(db)
    user.logout()
    session.pop('user_name', None)
    flash('已登出', 'info')
    return redirect(url_for('index'))

# 註冊頁面
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# 註冊處理
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
    return redirect(url_for('login_page'))  # 註冊後回登入頁
#In[2] Place
# 展示場所地圖
@app.route('/place')
def place_view():
    place_map = PlaceMap(db)
    place_html = place_map.generate_map_html()
    is_logged_in = 'user_id' in session
    return render_template('place.html', map_html=place_html, is_logged_in=is_logged_in)

# 場所詳細資料
@app.route('/place/detail/<place_id>')
def place_detail(place_id):
    place_map = PlaceMap(db)
    place = place_map.get_place_detail(place_id)
    if place:
        place['_id'] = str(place['_id'])
        return jsonify({"status": "success", "data": place})
    return jsonify({"status": "fail", "msg": "Place not found"})

# 預約場所
@app.route('/place/reserve', methods=['POST'])
def place_reserve():
    if 'user_id' not in session:
        return jsonify({'status': 'fail', 'msg': '請先登入'})
    place_id = request.json.get('place_id')
    reserve_info = request.json.get('reserve_info')  # {date, time, extra_info...}
    user_id = session['user_id']
    place_map = PlaceMap(db)
    place_map.reserve_spot(place_id, user_id, reserve_info)
    return jsonify({'status': 'success', 'msg': '預約成功！'})

#In[3] 寵物管理
from models.pets import PetManager
@app.route('/pets')
def pets():
    if 'user_id' not in session:
        flash('請先登入', 'warning')
        return redirect(url_for('login_page'))
    pet_manager = PetManager(db)
    user_id = session['user_id']
    pets = pet_manager.get_pets_of_user(user_id)
    return render_template('mypet.html', pets=pets)
# 寵物清單
@app.route('/api/pets/list')
def pet_list():
    if 'user_id' not in session:
        return jsonify({'success': False, 'msg': '未登入'})
    pets = PetManager(db).get_pets_of_user(session['user_id'])
    return jsonify({'success': True, 'pets': pets})
# 新增寵物
@app.route('/api/pets/add', methods=['POST'])
def add_pet():
    if 'user_id' not in session:
        return jsonify({'success': False, 'msg': '請先登入'}), 401
    data = request.get_json()
    pet_manager = PetManager(db)
    success, pet_id, msg = pet_manager.add_pet(session['user_id'], data)
    if success:
        return jsonify({'success': True, 'pet_id': pet_id})
    else:
        return jsonify({'success': False, 'msg': msg}), 400

# 編輯寵物
@app.route('/api/pets/update/<pet_id>', methods=['POST'])
def update_pet(pet_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'msg': '未登入'})
    update_data = request.get_json()
    result = PetManager(db).update_pet(session['user_id'], pet_id, update_data)
    if result:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'msg': '更新失敗'})

@app.route('/health')
def health():
    return render_template('health.html')

@app.route('/diet')
def diet():
    return render_template('diet.html')

@app.route('/reminder')
def reminder():
    return render_template('reminder.html')

#In[5] 預約寵物醫療服務
from models.medical_service import MedicalService

# 顯示和新增預約
@app.route('/medical/view', methods=['GET'])
def medical_view():
    if 'user_id' not in session:
        flash("請先登入查看預約", "warning")
        return redirect(url_for('login_page'))

    pet_id = request.args.get("pet_id")
    if not pet_id:
        flash("請選擇要查看的寵物", "warning")
        return redirect(url_for('pets'))

    service = MedicalService(db)

    filters = {
        "service_type": request.args.get("service_type"),
        "clinic_name": request.args.get("clinic_name"),
        "appointment_date": request.args.get("appointment_date")
    }
    filters = {k: v for k, v in filters.items() if v}

    services = service.list_pet_services(pet_id, filters)
    for s in services:
        s['_id'] = str(s['_id'])

    return render_template('medical_view.html', services=services, pet_id=pet_id)

@app.route('/medical/appointment', methods=['GET', 'POST'])
def medical_appointment():
    if 'user_id' not in session:
        flash("請先登入才能預約", "warning")
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        service = MedicalService(db)

        pet_id = request.form.get('pet_id')
        if not pet_id:
            flash("缺少寵物資訊", "danger")
            return redirect(url_for('pets'))

        service_type = request.form.get('service_type')
        vet_name = request.form.get('vet_name')
        clinic_name = request.form.get('clinic_name')
        appointment_str = request.form.get('appointment_time')
        appointment_time = datetime.strptime(appointment_str, "%Y-%m-%dT%H:%M")
        service_location = request.form.get('service_location')

        service.schedule_service(
            session['user_id'], pet_id, service_type, vet_name, clinic_name,
            appointment_time, service_location
        )
        flash("預約成功", "success")
        return redirect(url_for('medical_view', pet_id=pet_id))

    pet_id = request.args.get("pet_id")
    return render_template('medical_appointment.html', pet_id=pet_id)

# 刪除預約
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

    pet_id = request.form.get("pet_id", "")
    return redirect(url_for('medical_view', pet_id=pet_id))

# 修改預約
@app.route('/medical/edit/<service_id>', methods=['POST'])
def edit_medical(service_id):
    if 'user_id' not in session:
        flash("請先登入", "warning")
        return redirect(url_for('index'))

    pet_id = request.form.get('pet_id')

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
    return redirect(url_for('medical_view', pet_id=pet_id))

@app.route('/supplies')
def supplies():
    return render_template('supplies.html')

#In[8] 寵物活動與事件公告
from models.event import EventManager

@app.route('/event')
def event():
    if 'user_id' not in session:
        flash("請先登入", "warning")
        return redirect(url_for('login_page'))

    em = EventManager(db)

    selected_category = request.args.get("category")

    if selected_category and selected_category != "全部":
        all_events = em.get_all_events_by_category(selected_category)
    else:
        all_events = em.get_all_events()

    joined_events = em.get_user_signed_events(session['user_id'])
    joined_ids = {str(e['_id']) for e in joined_events}

    return render_template(
        'pet_event.html',
        events=all_events,
        joined_events=joined_events,
        joined_ids=joined_ids,
        selected_category=selected_category or "全部"
    )

@app.route('/event/signup/<event_id>', methods=['POST'])
def event_signup(event_id):
    if 'user_id' not in session:
        flash("請先登入", "warning")
        return redirect(url_for('login_page'))

    em = EventManager(db)
    success = em.signup_event(session['user_id'], event_id)

    if success:
        flash("報名成功", "success")
    else:
        flash("你已報名過此活動", "info")

    return redirect(url_for('event'))

@app.route('/event/cancel/<event_id>', methods=['POST'])
def event_cancel(event_id):
    if 'user_id' not in session:
        flash("請先登入", "warning")
        return redirect(url_for('login_page'))

    em = EventManager(db)
    success = em.cancel_signup(session['user_id'], event_id)

    if success:
        flash("已取消報名", "info")
    else:
        flash("取消失敗或尚未報名", "danger")

    return redirect(url_for('event'))

@app.route('/event/create', methods=['GET', 'POST'])
def event_create():
    if 'user_id' not in session:
        flash("請先登入", "warning")
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        data = {
            "event_name": request.form['event_name'],
            "event_time": request.form['event_time'],
            "event_location": request.form['event_location'],
            "event_description": request.form['event_description'],
            "event_organizer": request.form['event_organizer'],
            "max_participants": int(request.form['max_participants']),
            "category": request.form['category']
        }
        em = EventManager(db)
        em.create_event(data)
        flash("活動新增成功", "success")
        return redirect(url_for('event'))

    return render_template('event_create.html')

# AI智能助理
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

#In[4] Main function
if __name__ == '__main__':
    app.run(debug=True)