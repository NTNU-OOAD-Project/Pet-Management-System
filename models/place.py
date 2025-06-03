from abc import ABC, abstractmethod
from bson.objectid import ObjectId
import folium

class Place:
    def __init__(self, place_dict, color='blue', icon='info-sign'):
        self.place_id = place_dict.get("place_id")
        self.place_name = place_dict.get("place_name")
        self.place_type = place_dict.get("place_type")
        self.location = place_dict.get("location")
        self.facilities = place_dict.get("facilities", [])
        self.open_hours = place_dict.get("open_hours")
        self.latitude = float(place_dict.get("latitude"))
        self.longitude = float(place_dict.get("longitude"))
        self._id = str(place_dict.get("_id")) if "_id" in place_dict else None
        self.color = color
        self.icon = icon
    
    def get_popup_html(self):
        if self.place_type == "醫院":
            return (
                f"<b>場所名稱:</b> {self.place_name}<br>"
                f"<b>地址:</b> {self.location}<br>"
                f"<b>設施:</b> {', '.join(self.facilities)}<br>"
                f"<b>開放時間:</b> {self.open_hours}<br>"
                f'<a href="/medical/appointment?clinic={self.place_name}">預約診所</a>'
            )
        else:
            return (
                f"<b>場所名稱:</b> {self.place_name}<br>"
                f"<b>地址:</b> {self.location}<br>"
                f"<b>設施:</b> {', '.join(self.facilities)}<br>"
                f"<b>開放時間:</b> {self.open_hours}<br>"
                f"<button onclick=\"showPlaceDetail('{self._id}')\">詳細</button>"
            )


class PlaceManager:
    COLOR_ICON_MAP = {
        "公園":    ("green", "tree"),
        "醫院":    ("red", "plus-sign"),
        "餐廳":    ("orange", "cutlery"),
        "垃圾桶":  ("blue", "trash")
    }
    def __init__(self, db):
        self.db = db

    def get_all_places(self):
        places = list(self.db["places"].find({}))
        return [Place(
            p,
            *self.COLOR_ICON_MAP.get(p.get("place_type"), ("blue", "info-sign"))
        ) for p in places]

    def get_place_by_id(self, place_id):
        place = self.db["places"].find_one({"_id": ObjectId(place_id)})
        return Place(
            place,
            *self.COLOR_ICON_MAP.get(place.get("place_type"), ("blue", "info-sign"))
        ) if place else None

    def get_places_by_type(self, place_type):
        q = {} if place_type == "全部" else {"place_type": place_type}
        places = list(self.db["places"].find(q))
        return [Place(
            p,
            *self.COLOR_ICON_MAP.get(p.get("place_type"), ("blue", "info-sign"))
        ) for p in places]

    # 加一個可選參數 place_type
    def generate_folium_map(self, center=[25.033964, 121.564468], zoom_start=14, place_type="全部"):
        m = folium.Map(location=center, zoom_start=zoom_start)
        if place_type == "全部":
            places = self.get_all_places()
        else:
            places = self.get_places_by_type(place_type)
        for p in places:
            folium.Marker(
                location=[p.latitude, p.longitude],
                popup=p.get_popup_html(),
                tooltip=p.place_name,
                icon=folium.Icon(color=p.color, icon=p.icon)
            ).add_to(m)
        folium.LayerControl().add_to(m)
        from folium.plugins import LocateControl
        LocateControl().add_to(m)
        return m._repr_html_()