import os
from PyQt5.QtCore import Qt, QUrl, QObject, pyqtSignal
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QLabel, QLineEdit
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel


class Bridge(QObject):
    waypointAdded = pyqtSignal(float, float)  # 傳航點座標到 Python


class MapView(QMainWindow):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setWindowTitle("Simulator Map (MVC)")
        self.setGeometry(100, 100, 1280, 800)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        central.setLayout(layout)

        # Leaflet map webview
        self.webview = QWebEngineView()
        layout.addWidget(self.webview)

        # 建立 QWebChannel 橋接
        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.channel.registerObject("qtbridge", self.bridge)
        self.webview.page().setWebChannel(self.channel)

        # overlay control bar
        self._create_overlay_controls()
        self._load_map_html()

    def _create_overlay_controls(self):
        self.top_bar = QWidget(self)
        self.top_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.top_bar.setStyleSheet("background: rgba(0,0,0,0.5); color: white; border-radius: 6px;")
        h = QHBoxLayout()
        h.setContentsMargins(8, 6, 8, 6)
        self.top_bar.setLayout(h)

        self.lat_input = QLineEdit()
        self.lat_input.setFixedWidth(110)
        self.lat_input.setPlaceholderText("lat")
        self.lng_input = QLineEdit()
        self.lng_input.setFixedWidth(110)
        self.lng_input.setPlaceholderText("lng")
        add_btn = QPushButton("Add Marker")
        center_btn = QPushButton("Center Map")
        clear_btn = QPushButton("Clear Markers")

        h.addWidget(QLabel("Marker:"))
        h.addWidget(self.lat_input)
        h.addWidget(self.lng_input)
        h.addWidget(add_btn)
        h.addWidget(center_btn)
        h.addWidget(clear_btn)

        self.add_btn = add_btn
        self.center_btn = center_btn
        self.clear_btn = clear_btn

        self.top_bar.setFixedHeight(44)
        self.top_bar.move(12, 12)
        self.top_bar.show()

    def resizeEvent(self, event):
        self.top_bar.move(12, 12)
        super().resizeEvent(event)

    def _load_map_html(self):
        drone_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "picture", "drone.png"))
        drone_url = QUrl.fromLocalFile(drone_path).toString()
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
            <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
            <style>
                html, body, #map {{ height: 100%; margin: 0; }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([22.9048880, 120.2719823], 20);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors'
                }}).addTo(map);

                var markers = {{}};
                
                // 無人機圖示
                var droneIcon = L.icon({{
                    iconUrl: '{drone_url}',
                    iconSize: [48, 48],
                    iconAnchor: [24, 24],
                    popupAnchor: [0, -24]
                }});
    
                var droneMarker = L.marker([22.9048880, 120.2719823], {{icon: droneIcon}}).addTo(map);
                droneMarker.bindPopup("無人機位置");

                function addMarker(id, lat, lng, label) {{
                    var m = L.marker([lat, lng]).addTo(map);
                    if(label) m.bindPopup(label);
                    markers[id] = m;
                }}

                function setCenter(lat, lng, zoom) {{
                    map.setView([lat, lng], zoom || map.getZoom());
                }}

                function clearMarkers() {{
                    for(var k in markers){{
                        map.removeLayer(markers[k]);
                    }}
                    markers = {{}};
                }}

                // 右鍵點擊 -> 加航點並回傳 Python
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    window.qtbridge = channel.objects.qtbridge;
                }});

                map.on('contextmenu', function(e) {{
                    var lat = e.latlng.lat;
                    var lng = e.latlng.lng;
                    var m = L.marker([lat, lng]).addTo(map);
                    m.bindPopup("航點<br>Lat: " + lat.toFixed(6) + "<br>Lng: " + lng.toFixed(6)).openPopup();
                    if(window.qtbridge) {{
                        window.qtbridge.waypointAdded(lat, lng);
                    }}
                }});
            </script>
        </body>
        </html>
        """
        self.webview.setHtml(html, baseUrl=QUrl.fromLocalFile(os.path.dirname(drone_path) + "/"))

    def run_js(self, js_code, callback=None):
        """在 QWebEngineView 執行 JavaScript，可選擇是否處理回傳值"""
        if callback:
            self.webview.page().runJavaScript(js_code, callback)
        else:
            self.webview.page().runJavaScript(js_code)
