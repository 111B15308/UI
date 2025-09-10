from PyQt5.QtCore import QObject

class MapController(QObject):
    def __init__(self, model, view):
        super().__init__()
        self.model = model
        self.view = view

        # connect UI buttons
        self.view.add_btn.clicked.connect(self.on_add_marker_clicked)
        self.view.center_btn.clicked.connect(self.on_center_clicked)
        self.view.clear_btn.clicked.connect(self.on_clear_markers)

        # connect from JS (右鍵航點)
        self.view.bridge.waypointAdded.connect(self.on_waypoint_added)

        # sync model changes
        self.model.state_changed.connect(self.sync_model_to_view)
        self.sync_model_to_view()

    def sync_model_to_view(self):
        c = self.model.center
        z = self.model.zoom
        self.view.run_js(f"setCenter({c['lat']}, {c['lng']}, {z});")
        self.view.run_js("clearMarkers();")
        for m in self.model.markers:
            label = (m.get("label") or "").replace("'", "\\'")
            js = f"addMarker('{m['id']}', {m['lat']}, {m['lng']}, '{label}');"
            self.view.run_js(js)

    def on_add_marker_clicked(self):
        try:
            lat = float(self.view.lat_input.text())
            lng = float(self.view.lng_input.text())
        except ValueError:
            return
        marker = {
            "id": f"m{len(self.model.markers)+1}",
            "lat": lat, "lng": lng,
            "label": str(len(self.model.markers)+1)
        }
        self.model.add_marker(marker)

    def on_center_clicked(self):
        try:
            lat = float(self.view.lat_input.text())
            lng = float(self.view.lng_input.text())
        except ValueError:
            return
        self.model.center = {"lat": lat, "lng": lng}

    def on_clear_markers(self):
        self.model.clear_markers()

    def on_waypoint_added(self, lat, lng):
        """由地圖右鍵新增航點時呼叫"""
        marker = {
            "id": f"m{len(self.model.markers)+1}",
            "lat": lat, "lng": lng,
            "label": f"WP{len(self.model.markers)+1}"
        }
        self.model.add_marker(marker)
