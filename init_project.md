## 專案初始化
### 資料庫建置
    1. 首先要下載MongoDB Compass(直觀的interface), 然後確認連線的port
    2. 建立.env, 上面要有:
        ```
        MONGODB_URI=mongodb://localhost:*/ // *=Port Number
        MONGODB_DB=OOAD_pet_daily
        
        ```
    3. 建立需要的collections: 例如 users, places等等, **如果有新增collections，一定要通知大家名稱**

### Flask
```bash
python app.py
```
應該就可以run了