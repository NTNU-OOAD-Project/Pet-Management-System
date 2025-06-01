#In[0] Initialization
from flask import Flask, render_template, session, jsonify, request, flash, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
from models.place import PlaceMap
from dotenv import load_dotenv
from services.notification_service import NotificationService
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

#.env file
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB = os.getenv('MONGODB_DB')


client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]


@app.route('/')
def index():
    return render_template('index.html')

@app.context_processor
def inject_unread_notification_count():
    user_service = User(db)
    current_user = user_service.get_current_user()

    if current_user:
        notif_service = NotificationService(db)
        unread_count = notif_service.get_unread_count(current_user['_id'])
    else:
        unread_count = 0

    return dict(unread_count=unread_count)

#In[1] User Management
from models.user import User
@app.route('/login', methods=['POST'])
def login():
    user = User(db)
    email = request.form.get('email')
    password = request.form.get('password')
    success, msg = user.login(email, password)
    if success:
        flash('登入成功', 'success')
        return redirect(url_for('index'))
    else:
        flash(msg, 'danger')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    user = User(db)
    user.logout()
    flash('已登出', 'info')
    return redirect(url_for('index'))

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
    return redirect(url_for('index'))
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
@app.route('/pets')
def pets():
    return render_template('pets.html')

@app.route('/health')
def health():
    return render_template('health.html')

@app.route('/diet')
def diet():
    return render_template('diet.html')

@app.route('/reminder')
def reminder():
    return render_template('reminder.html')

@app.route('/medical')
def medical():
    return render_template('medical.html')

@app.route('/supplies')
def supplies():
    return render_template('supplies.html')

#In[4] 活動預約
@app.route('/event')
def event():
    return render_template('event.html')

#In[5] 寵物飲食紀錄管理
@app.route('/diet/view')
def view_diet_records():
    records_cursor = db.diet_records.find()
    records = []
    for rec in records_cursor:
        rec['_id'] = str(rec['_id'])
        records.append(rec)
    return render_template('diet_records.html', records=records)

@app.route('/diet/add', methods=['GET', 'POST'])
def add_diet_record():
    if request.method == 'POST':
        pet_id = request.form.get('pet_id')
        food = request.form.get('food')
        amount = float(request.form.get('amount'))

        record = record.record_manager.create_record("diet", pet_id=pet_id, food=food, amount=amount)
        record.record_manager.add_record(record)
        db.diet_records.insert_one(record.to_dict())

        flash("飲食紀錄新增成功！", "success")
        return redirect(url_for('view_diet_records'))

    return render_template('diet_add.html')

@app.route('/diet/delete/<record_id>', methods=['POST'])
def delete_diet_record(record_id):
    db.diet_records.delete_one({'_id': ObjectId(record_id)})
    flash("記錄已刪除", "info")
    return redirect(url_for('view_diet_records'))

@app.route('/diet/edit/<record_id>', methods=['GET', 'POST'])
def edit_diet_record(record_id):


    if request.method == 'POST':
        food = request.form.get('food')
        amount = float(request.form.get('amount'))
        db.diet_records.update_one(
            {'_id': ObjectId(record_id)},
            {'$set': {'food': food, 'amount': amount}}
        )
        flash("記錄已更新", "success")
        return redirect(url_for('view_diet_records'))

    # GET：顯示原始資料
    record = db.diet_records.find_one({'_id': ObjectId(record_id)})
    record['_id'] = str(record['_id'])
    return render_template('diet_edit.html', record=record)



#In[4] Main function
if __name__ == '__main__':
    app.run(debug=True)

