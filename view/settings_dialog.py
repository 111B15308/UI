from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QVBoxLayout

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("無人機參數設定")

        layout = QVBoxLayout()
        form = QFormLayout()

        self.port_input = QLineEdit()
        self.ip_input = QLineEdit()
        self.spacing_input = QLineEdit()
        self.alt_step_input = QLineEdit()
        self.rtl_height_input = QLineEdit()
        self.speed_input = QLineEdit()

        form.addRow("Port:", self.port_input)
        form.addRow("IP:", self.ip_input)
        form.addRow("間隔 (Spacing):", self.spacing_input)
        form.addRow("高度間隔 (Alt Step):", self.alt_step_input)
        form.addRow("RTL 高度:", self.rtl_height_input)
        form.addRow("速度:", self.speed_input)

        layout.addLayout(form)

        ok_btn = QPushButton("確定")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)

        self.setLayout(layout)

    def get_settings(self):
        return {
            "port": self.port_input.text(),
            "ip": self.ip_input.text(),
            "spacing": self.spacing_input.text(),
            "alt_step": self.alt_step_input.text(),
            "rtl_height": self.rtl_height_input.text(),
            "speed": self.speed_input.text(),
        }
