import os
from PyQt5.QtCore import Qt, QUrl, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QLabel, QLineEdit
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel


class Bridge(QObject):
    # Python 內部 signal，Controller 會接它
    waypointAdded = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()

    # JS 會呼叫這個 slot -> Python 再 emit signal，Controller 監聽 signal
    @pyqtSlot(float, float)
    def addWaypoint(self, lat, lng):
        # emit to Python listeners
        self.waypointAdded.emit(lat, lng)


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

        # overlay control bar (保留但可以隱藏，不會造成屬性找不到)
        self._create_overlay_controls()
        self.top_bar.hide()  # 隱藏黑框（如果要顯示改成 show()）

        # 載入地圖 HTML（非同步）
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
        # 移動 top_bar（如果被顯示）
        try:
            self.top_bar.move(12, 12)
        except Exception:
            pass
        super().resizeEvent(event)

    def _load_map_html(self):
        # drone path may be missing — guard it
        drone_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "picture", "drone.png"))
        if os.path.exists(drone_path):
            drone_url = QUrl.fromLocalFile(drone_path).toString()
        else:
            drone_url = ""  # 空字串不會崩潰

        # HTML with JS functions and debug logs
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
                console.log("js: start script"); // debug - should appear in app console

                // initialize map
                var map = L.map('map').setView([22.9048880, 120.2719823], 20);
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors'
                }}).addTo(map);
                console.log("js: leaflet tile added");

                var markers = {{}};
                var polylines = [];

                // optional drone icon
                var droneIcon = null;
                var drone_url = "{drone_url}";
                if (drone_url) {{
                    droneIcon = L.icon({{
                        iconUrl: drone_url,
                        iconSize: [48,48],
                        iconAnchor: [24,24],
                        popupAnchor: [0,-24]
                    }});
                    var droneMarker = L.marker([22.9048880, 120.2719823], {{icon: droneIcon}}).addTo(map);
                    droneMarker.bindPopup("無人機位置");
                }}

                // exposed functions for Python controller
                function addMarker(id, lat, lng, label) {{
                    var m = L.marker([lat, lng]).addTo(map);
                    if (label) {{
                        m.bindTooltip(label, {{permanent: false, direction: "top"}});
                        m.bindPopup(label);
                    }}
                    markers[id] = m;
                }}

                function setCenter(lat, lng, zoom) {{
                    console.log("js: setCenter", lat, lng, zoom);
                    map.setView([lat, lng], zoom || map.getZoom());
                }}

                function clearMarkers() {{
                    console.log("js: clearMarkers");
                    for (var k in markers) {{
                        try {{ map.removeLayer(markers[k]); }} catch(e){{}}
                    }}
                    markers = {{}};
                }}

                function drawPath(coords) {{
                    // remove old lines
                    for (var i = 0; i < polylines.length; i++) {{
                        try {{ map.removeLayer(polylines[i]); }} catch(e){{}}
                    }}
                    polylines = [];

                    if (coords && coords.length > 1) {{
                        var line = L.polyline(coords, {{color: 'blue'}}).addTo(map);
                        polylines.push(line);
                    }}
                }}

                // QWebChannel init (expose qtbridge)
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    window.qtbridge = channel.objects.qtbridge;
                    console.log("js: qtbridge ready:", !!window.qtbridge);
                }});

                // right-click (contextmenu) adds a visual marker and tells Python via qtbridge.addWaypoint
                map.on('contextmenu', function(e) {{
                    var lat = e.latlng.lat;
                    var lng = e.latlng.lng;
                    var m = L.marker([lat, lng]).addTo(map);
                    m.bindPopup("航點<br>Lat: " + lat.toFixed(6) + "<br>Lng: " + lng.toFixed(6)).openPopup();
                    if (window.qtbridge && typeof window.qtbridge.addWaypoint === 'function') {{
                        window.qtbridge.addWaypoint(lat, lng);
                    }} else {{
                        console.log("js: qtbridge.addWaypoint not available yet");
                    }}
                }});
                console.log("js: script end");
            </script>
        </body>
        </html>
        """
        # set HTML (baseUrl so local files like drone.png load)
        base = QUrl.fromLocalFile(os.path.dirname(drone_path) + "/") if drone_url else QUrl()
        self.webview.setHtml(html, baseUrl=base)

    def run_js(self, js_code, callback=None):
        """在 QWebEngineView 執行 JavaScript，可選擇是否處理回傳值"""
        if callback:
            self.webview.page().runJavaScript(js_code, callback)
        else:
            self.webview.page().runJavaScript(js_code)
