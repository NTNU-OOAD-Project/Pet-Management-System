from abc import ABC, abstractmethod
from bson.objectid import ObjectId
import folium

class BasePlaceLayer(ABC):
    def __init__(self, db, type_name, layer_name, color, icon):
        self.db = db
        self.type_name = type_name
        self.layer_name = layer_name
        self.color = color
        self.icon = icon

    @abstractmethod
    def add_layer(self, map_osm):
        pass

class TypedPlaceLayer(BasePlaceLayer):
    def add_layer(self, map_osm):
        # 只撈該類型
        places = list(self.db["places"].find(
            {"place_type": self.type_name}
        ))
        layer = folium.FeatureGroup(name=self.layer_name)
        for item in places:
            try:
                popup_html = (
                    f"<b>場所名稱:</b> {item.get('place_name', '')}<br>"
                    f"<b>地址:</b> {item.get('location', '')}<br>"
                    f"<b>設施:</b> {item.get('facilities', '')}<br>"
                    f"<b>開放時間:</b> {item.get('open_hours', '')}<br>"
                    f"<button onclick=\"showPlaceDetail('{str(item['_id'])}')\">詳細</button>"
                )
                folium.Marker(
                    location=[float(item['latitude']), float(item['longitude'])],
                    popup=popup_html,
                    tooltip=item.get("place_name", self.layer_name),
                    icon=folium.Icon(color=self.color, icon=self.icon)
                ).add_to(layer)
            except (ValueError, TypeError, KeyError):
                print(f"跳過無效場所資料: {item}")
        layer.add_to(map_osm)

class PlaceMap:
    def __init__(self, db):
        # 建立四個 layer，類型、地圖名稱、顏色、icon
        self.layers = [
            TypedPlaceLayer(db, "公園", "公園地圖", "green", "tree"),
            TypedPlaceLayer(db, "醫院", "寵物醫院地圖", "red", "heartbeat"),
            TypedPlaceLayer(db, "垃圾桶", "垃圾桶地圖", "blue", "trash"),
            TypedPlaceLayer(db, "餐廳", "餐廳地圖", "orange", "cutlery")
        ]

    def generate_map_html(self):
        map_osm = folium.Map(location=[25.033964, 121.564468], zoom_start=14)
        for layer in self.layers:
            layer.add_layer(map_osm)
        folium.LayerControl().add_to(map_osm)
        from folium.plugins import LocateControl
        LocateControl().add_to(map_osm)
        return map_osm._repr_html_()
     
    def get_place_detail(self, place_id):
        # 以 place_id 查詢場所詳細資料
        return self.db["places"].find_one({"_id": ObjectId(place_id)})

    def reserve_spot(self, place_id, user_id, reserve_info):
        reservation = {
            "place_id": place_id,
            "user_id": user_id,
            "reserve_info": reserve_info
        }
        self.db["place_reservations"].insert_one(reservation)
        return True
