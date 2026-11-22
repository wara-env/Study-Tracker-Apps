from PySide6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
)

from api import ApiError


class LoginDialog(QDialog):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self.setWindowTitle("Study Tracker — Masuk")
        self.setMinimumWidth(320)

        self.user = QLineEdit()
        self.pw = QLineEdit()
        self.pw.setEchoMode(QLineEdit.Password)
        self.pw.returnPressed.connect(self.do_login)

        form = QFormLayout()
        form.addRow("Username", self.user)
        form.addRow("Password", self.pw)

        login_btn = QPushButton("Masuk")
        login_btn.setDefault(True)
        login_btn.clicked.connect(self.do_login)
        reg_btn = QPushButton("Daftar")
        reg_btn.clicked.connect(self.do_register)
        row = QHBoxLayout()
        row.addWidget(reg_btn)
        row.addWidget(login_btn)

        self.status = QLabel("")
        self.status.setObjectName("error")

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(self.status)
        lay.addLayout(row)

    def _run(self, fn):
        try:
            fn(self.user.text().strip(), self.pw.text())
        except ApiError as e:
            self.status.setText(str(e))
            return
        self.accept()

    def do_login(self):
        self._run(self.api.login)

    def do_register(self):
        self._run(self.api.register)
