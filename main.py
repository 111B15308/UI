import os
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
os.environ["QTWEBENGINE_PROFILE"] = "D:/QtCache"

import sys
from PyQt5.QtWidgets import QApplication, QDialog

# 原 MVC 模組
from model.model import MapModel
from view.view import MapView
from controller.controller import MapController

# 新增設定視窗
from view.settings_dialog import SettingsDialog


def main():
    app = QApplication(sys.argv)

    # --- 啟動時先顯示設定視窗 ---
    settings_dialog = SettingsDialog()
    if settings_dialog.exec_() == QDialog.Accepted:
        settings = settings_dialog.get_settings()

        # --- 建立 Model 並存入無人機設定 ---
        model = MapModel()
        if hasattr(model, "set_drone_settings"):
            model.set_drone_settings(settings)

        # --- 建立 View 和 Controller ---
        view = MapView(model)
        controller = MapController(model, view)

        view.show()
        sys.exit(app.exec_())
    else:
        # 如果使用者取消設定，直接退出程式
        sys.exit(0)


if __name__ == "__main__":
    main()
