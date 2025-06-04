#In[0] Initialization =======================================================================
from flask import Flask, session, request, render_template, jsonify, flash, redirect, url_for, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone
from models.services.record_manager import RecordManager
from bson import ObjectId
# import scheduler
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

#In[1] User Management =======================================================================
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
#In[2] Place =======================================================================
# 展示場所地圖
from models.place import PlaceManager
place_manager = PlaceManager(db)
@app.route('/place_display')
def place_display():
    # 使用 PlaceManager 產生 folium map html
    place_html = place_manager.generate_folium_map()
    is_logged_in = 'user_id' in session
    return render_template('pet_place.html', map_html=place_html, is_logged_in=is_logged_in)

# 場所詳細資料
@app.route('/place/detail/<place_id>')
def place_detail(place_id):
    place = place_manager.get_place_by_id(place_id)
    if place:        
        data = {
            "_id": place._id,
            "place_id": place.place_id,
            "place_name": place.place_name,
            "place_type": place.place_type,
            "location": place.location,
            "facilities": place.facilities,
            "open_hours": place.open_hours,
            "latitude": place.latitude,
            "longitude": place.longitude
        }
        return jsonify({"status": "success", "data": data})
    return jsonify({"status": "fail", "msg": "Place not found"})

# 場所分類
@app.route('/api/places/filter/<place_type>')
def filter_places(place_type):
    # place_type 分類 "公園", "醫院", "餐廳", "垃圾桶", "全部"
    map_html = place_manager.generate_folium_map(place_type=place_type)
    return jsonify({"map_html": map_html})

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

#In[3] 寵物管理 =======================================================================
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

#In[4] 寵物健康紀錄 =======================================================================

@app.route('/health')
def health():
    pet_id = request.args.get('pet_id')
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login_page'))  # 或回傳 401
    if not pet_id:
        return "缺少 pet_id", 400

    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return "找不到使用者", 404

    pet = next((p for p in user.get("pets", []) if p["pet_id"] == pet_id), None)
    if not pet:
        return "找不到寵物", 404

    health_records = pet.get("health_records", [])
    health = health_records[-1] if health_records else {}

    return render_template("health_record_view.html", health=health, pet=pet, pet_id=pet_id)


@app.route("/health/edit")
def health_edit():
    pet_id = request.args.get("pet_id")
    user_id = session.get("user_id")
    if not pet_id or not user_id:
        return redirect(url_for("pets"))

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return redirect(url_for("pets"))

    pet = next((p for p in user.get("pets", []) if p["pet_id"] == pet_id), None)
    if not pet:
        return redirect(url_for("pets"))

    health_records = pet.get("health_records", [])
    latest = health_records[-1] if health_records else None

    # 帶入 pet 與最新健康紀錄、pet_id
    return render_template("health_record.html", pet=pet, record=latest, pet_id=pet_id)
    

@app.route("/api/health/update", methods=["POST"])
def update_health_record():
    try:
        data = request.get_json()
        record_id = data.get("_id")

        record_id = data.get("_id")
        if not record_id:
            return jsonify({"success": False, "msg": "缺少紀錄 ID (_id)"})
        RecordManager.update_record(
            record_id=ObjectId(record_id),
            type_str="health",
            update_fields=data,
            db=db
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})

#In[5] 寵物飲食 =======================================================================
@app.route('/diet')
def diet_view():
    pet_id = request.args.get('pet_id')
    user_id = session.get('user_id')

    
    # pet_id = test_pet_id                 # 臨時測試

    if not user_id:
        return "未登入", 401
    if not pet_id:
        return "缺少 pet_id", 400

    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return "找不到使用者", 404

    # 找出該寵物
    pet = next((p for p in user.get("pets", []) if p["pet_id"] == pet_id), None)
    if not pet:
        return "找不到寵物", 404

    diet_records = pet.get("diet_records", [])

    return render_template("health_record_view.html", diet_records=diet_records)


#編輯頁面
@app.route('/diet/edit')
def diet_edit():    

    pet_id = request.args.get('pet_id')
    user_id = session.get('user_id')

    if not user_id:
        return "未登入", 401
    if not pet_id:
        return "缺少 pet_id", 400

    user = db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        return "找不到使用者", 404

    pet = next((p for p in user.get("pets", []) if p["pet_id"] == pet_id), None)
    if not pet:
        return "找不到寵物", 404

    diet_records = pet.get("diet_records", [])
    return render_template("diet_edit.html", diet_records=diet_records, pet_id=pet_id)



#儲存紀錄(確認編輯)
@app.route('/api/diet/save_batch', methods=['POST'])
def save_diet_records_batch():
    user_id = session.get("user_id")
    pet_id = request.args.get('pet_id')
    data = request.get_json()  # 接收一個列表

    if not user_id or not isinstance(data, list):
        return jsonify({"success": False, "msg": "格式錯誤或未登入"}), 400

    record_manager = RecordManager()
    created, updated = 0, 0
    for entry in data:
        record_id = entry.get("_id")
        try:
            if record_id:
                try:
                    record_manager.update_record(
                        record_id=ObjectId(record_id),
                        type_str="diet",
                        update_fields=entry,
                        db=db
                    )
                    updated += 1
                    continue
                except ValueError:
                    pass  # 如果找不到記錄則當作新增

            # 新增
            entry["pet_id"] = pet_id
            record_manager.add_record_by_type(
                type_str="diet",
                data=entry,
                db=db
            )
            created += 1

        except Exception as e:
            print(f"處理失敗: {e}")
            continue

    return jsonify({
        "success": True,
        "created": created,
        "updated": updated
    })


#刪除紀錄
@app.route("/api/diet/delete", methods=["POST"])
def delete_diet_record():
    user_id = session.get("user_id")
    data = request.get_json()
    record_id = data.get("record_id")

    if not user_id:
        return jsonify({"success": False, "msg": "未登入"}), 401
    if not record_id:
        return jsonify({"success": False, "msg": "缺少記錄 ID"}), 400

    try:
        record_manager = RecordManager()
        record_manager.delete_record(ObjectId(record_id), "diet", db)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500
#In[6] 寵物照護提醒 =======================================================================

from flask import Blueprint, request, render_template
from bson import ObjectId

@app.route("/care_reminder", methods=["GET"])
def care_reminder_page():
    pet_id = request.args.get("pet_id")
    # pet_id = test_pet_id      #測試用(目前寵物的list沒有讀到)

    if not pet_id:
        return "缺少 pet_id", 400

    user = db.users.find_one({"pets.pet_id": pet_id})
    if not user:
        return "找不到對應的寵物", 404

    for pet in user["pets"]:
        if pet["pet_id"] == pet_id:
            reminders = pet.get("remind_records", [])
            return render_template("care_reminder_view.html", reminders=reminders, pet_id = pet_id)
    return render_template("test.html", reminders=[])

#開關提醒
@app.route('/api/reminder/active', methods=['PATCH'])
def update_active_state():
    data = request.get_json()
    record_id = data.get("record_id")
    active = data.get("active")

    if not record_id or active is None:
        return jsonify({"success": False, "error": "缺少參數"}), 400

    result = db.users.update_one(
        { "pets.remind_records._id": ObjectId(record_id) },
        { "$set": { "pets.$[].remind_records.$[r].active": active } },
        array_filters=[{ "r._id": ObjectId(record_id) }]
    )

    if result.modified_count == 0:
        return jsonify({"success": False, "error": "未更新任何資料"}), 404

    return jsonify({"success": True})

#編輯畫面
@app.route("/care_reminder/edit")
def care_reminder_edit():
    pet_id = request.args.get("pet_id")
    user_id = session.get("user_id")
    if not user_id:
        return "找不到使用者", 404

    # ⬇ 這行是關鍵：用 user_id 找到整份使用者資料
    user = db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return "找不到使用者", 404

    for pet in user.get("pets", []):
        if str(pet["pet_id"]) == pet_id:
            reminders = pet.get("remind_records", [])
            return render_template("care_reminder.html", reminders=reminders, pet_id=pet_id )

    return "找不到寵物", 404


# 儲存提醒資料
@app.route("/api/save-reminders", methods=["POST"])
def save_care_reminder():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "請先登入"}), 401

    data = request.get_json()
    updates = data.get("updates", [])
    print("哈囉",updates)
    record_manager = RecordManager()
    updated = 0

    for entry in updates:
        try:
            record_id = entry.get("_id")
            pet_id = entry.get("pet_id")
            if not record_id:
                record_manager.add_record_by_type(
                    type_str="remind",
                    data=entry,
                    db=db
                )
            else:
                record_manager.update_record(
                    record_id=record_id,
                    type_str="remind",
                    update_fields=entry,
                    db=db
                )
            updated += 1
        except Exception as e:
            print("新增錯誤：", e)

    return jsonify({
        "success": True,
        "updated": updated,
        "pet_id":pet_id
    })


#In[7] 預約寵物醫療服務 =======================================================================
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

#In[7] 用品庫存
@app.route("/supply")
def supply_view():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return "找不到使用者", 404

    inventories = user.get("inventory", [])
    inventory_data = []

    for inv in inventories:
        _id = str(inv.get("_id"))
        item_name = inv.get("item_name")
        quantity = inv.get("quantity")
        threshold = inv.get("threshold")

        inventory_data.append({
            "_id": _id,
            "item_name": item_name,
            "quantity": quantity,
            "threshold": threshold,
        })

    return render_template("supply_view.html", inventory_list=inventory_data)


#歷史紀錄清單
@app.route("/supply/history")
def supply_history():
    user_id = session.get("user_id")
    inventory_id = request.args.get("inventory_id") 

    if not user_id or not inventory_id:
        return "缺少參數或未登入", 400

    try:
        records = RecordManager().view_by_type(db, inventory_id, "inventory", user_id)
    except ValueError as e:
        return str(e), 404

    parsed_records = []

    for record in records:
        parsed_records.append({
            "record_id": str(record.get("_id", "")),
            "delta_quantity": record.get("delta_quantity"),
            "reason": record.get("reason"),
            "date": record.get("date"),
            "user_id": str(record.get("user_id", ""))
        })

    return render_template("supply_history.html", records=parsed_records, inventory_id=inventory_id)

#刪除歷史紀錄
@app.route('/api/supply/delete', methods=['POST'])
def delete_supply_record():
    data = request.get_json()
    record_id = data.get("record_id")

    if not record_id:
        return jsonify({'success': False, 'msg': '缺少 record_id'}), 400

    try:
        record_manager.delete_record(ObjectId(record_id), "inventory", db)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'msg': str(e)}), 500

#回傳需編輯的資料
@app.route("/supply/history/edit")
def supply_edit():
    record_id = request.args.get("record_id")
    user_id = session.get("user_id")
    if not record_id or not user_id:
        return "缺少 record_id 或未登入", 400
    try:
        record = record_manager.find_record_by_id(ObjectId(record_id), "inventory", db)
        if not record:
            return "找不到紀錄", 404

        return render_template("supply_edit.html", record=record.to_dict())
    except Exception as e:
        return f"發生錯誤：{str(e)}", 500
    
#儲存編輯
@app.route("/api/supply/update", methods=["POST"])
def update_supply_record():
    data = request.get_json()
    record_id = data.get("record_id")
    update_fields = {
        "reason": data.get("reason"),
        "delta_quantity": data.get("delta_quantity"),
        "date": data.get("date")
    }

    try:
        record_manager.update_record(ObjectId(record_id), "inventory", update_fields, db)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})

#新增庫存
@app.route("/api/supply/add", methods=["POST"])
def add_inventory_record():
    data = request.get_json()
    try:
        record_manager.add_record_by_type("inventory", data, db)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})

#刪除庫存
@app.route('/api/inventory/delete', methods=['POST'])
def delete_inventory():
    data = request.get_json()
    inventory_id = data.get('inventory_id')

    if not inventory_id:
        return jsonify({"success": False, "msg": "缺少 inventory_id"})

    try:
        result = db.users.update_one(
            {"inventory._id": ObjectId(inventory_id)},
            {"$pull": {"inventory": {"_id": ObjectId(inventory_id)}}}
        )
        if result.modified_count > 0:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "msg": "刪除失敗或找不到紀錄"})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)})

#In[8] 寵物活動與事件公告 =======================================================================
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

#In[9] AI智能助理 =======================================================================
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

#In[10] Main function =======================================================================
if __name__ == '__main__':
    app.run(debug=True)