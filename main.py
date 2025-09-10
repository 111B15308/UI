import os
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
os.environ["QTWEBENGINE_PROFILE"] = "D:/QtCache"
import sys
from PyQt5.QtWidgets import QApplication
# ✅ 從子資料夾匯入
from model.model import MapModel
from view.view import MapView
from controller.controller import MapController


def main():
    app = QApplication(sys.argv)

    model = MapModel()
    view = MapView(model)
    controller = MapController(model, view)

    view.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

