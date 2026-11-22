from datetime import datetime

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QDateTimeEdit, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from api import ApiError


class TasksTab(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api

        self.title = QLineEdit()
        self.title.setPlaceholderText("Judul tugas...")
        self.title.returnPressed.connect(self.add)
        self.use_deadline = QCheckBox("Deadline")
        self.deadline = QDateTimeEdit(QDateTime.currentDateTime().addDays(1))
        self.deadline.setCalendarPopup(True)
        self.deadline.setDisplayFormat("dd MMM yyyy HH:mm")
        self.deadline.setEnabled(False)
        self.use_deadline.toggled.connect(self.deadline.setEnabled)
        add_btn = QPushButton("Tambah")
        add_btn.clicked.connect(self.add)

        self.list = QListWidget()
        self.list.itemChanged.connect(self.on_check)
        del_btn = QPushButton("Hapus terpilih")
        del_btn.clicked.connect(self.delete)

        top = QHBoxLayout()
        top.addWidget(self.title, 1)
        top.addWidget(self.use_deadline)
        top.addWidget(self.deadline)
        top.addWidget(add_btn)

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.list, 1)
        lay.addWidget(del_btn)

    def _err(self, e):
        QMessageBox.warning(self, "Error", str(e))

    def refresh(self):
        try:
            tasks = self.api.tasks()
        except ApiError as e:
            return self._err(e)
        self.list.blockSignals(True)
        self.list.clear()
        now = datetime.now()
        for t in tasks:
            text = t["title"]
            overdue = False
            if t["deadline"]:
                dl = datetime.fromisoformat(t["deadline"])
                text += f"   — {dl.strftime('%d %b %Y %H:%M')}"
                overdue = dl < now and not t["done"]
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if t["done"] else Qt.Unchecked)
            item.setData(Qt.UserRole, t["id"])
            if overdue:
                item.setForeground(QColor("#f87171"))
            elif t["done"]:
                item.setForeground(QColor("#64748b"))
            self.list.addItem(item)
        self.list.blockSignals(False)

    def add(self):
        title = self.title.text().strip()
        if not title:
            return
        dl = self.deadline.dateTime().toString(Qt.ISODate) if self.use_deadline.isChecked() else None
        try:
            self.api.add_task(title, dl)
        except ApiError as e:
            return self._err(e)
        self.title.clear()
        self.refresh()

    def on_check(self, item):
        try:
            self.api.update_task(item.data(Qt.UserRole), done=item.checkState() == Qt.Checked)
        except ApiError as e:
            return self._err(e)
        self.refresh()

    def delete(self):
        item = self.list.currentItem()
        if not item:
            return
        try:
            self.api.delete_task(item.data(Qt.UserRole))
        except ApiError as e:
            return self._err(e)
        self.refresh()
