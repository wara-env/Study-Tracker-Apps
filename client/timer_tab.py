from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QPushButton, QSpinBox,
    QVBoxLayout, QWidget,
)

from api import ApiError


class TimerTab(QWidget):
    """Pomodoro: fokus -> istirahat. Sesi fokus yang selesai otomatis dicatat ke server."""

    def __init__(self, api):
        super().__init__()
        self.api = api
        self.phase = "fokus"  # atau "istirahat"
        self.remaining = 0
        self.running = False

        self.subject = QComboBox()
        self.new_subject = QPushButton("+ Mata kuliah")
        self.new_subject.clicked.connect(self.add_subject)
        self.focus_min = QSpinBox(); self.focus_min.setRange(1, 180); self.focus_min.setValue(25)
        self.break_min = QSpinBox(); self.break_min.setRange(1, 60); self.break_min.setValue(5)
        self.focus_min.valueChanged.connect(self.reset)
        self.focus_min.setMaximumWidth(120); self.break_min.setMaximumWidth(120)

        self.phase_lbl = QLabel("FOKUS")
        self.phase_lbl.setObjectName("phase")
        self.phase_lbl.setAlignment(Qt.AlignCenter)
        self.clock = QLabel("25:00")
        self.clock.setObjectName("clock")
        self.clock.setAlignment(Qt.AlignCenter)
        self.today = QLabel("")
        self.today.setObjectName("hint")
        self.today.setAlignment(Qt.AlignCenter)

        self.start_btn = QPushButton("Mulai")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.toggle)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset)

        self.ticker = QTimer(self)
        self.ticker.setInterval(1000)
        self.ticker.timeout.connect(self.tick)

        form = QFormLayout()
        subj_row = QHBoxLayout()
        subj_row.addWidget(self.subject, 1)
        subj_row.addWidget(self.new_subject)
        form.addRow("Mata kuliah", subj_row)
        form.addRow("Fokus (menit)", self.focus_min)
        form.addRow("Istirahat (menit)", self.break_min)

        btns = QHBoxLayout()
        btns.addWidget(self.start_btn)
        btns.addWidget(self.reset_btn)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addStretch(1)
        lay.addWidget(self.phase_lbl)
        lay.addWidget(self.clock)
        lay.addLayout(btns)
        lay.addWidget(self.today)
        lay.addStretch(1)

        self.session_count = 0
        self.reset()

    # data
    def refresh(self):
        try:
            subjects = self.api.subjects()
        except ApiError as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        current = self.subject.currentData()
        self.subject.clear()
        for s in subjects:
            self.subject.addItem(s["name"], s["id"])
        if current is not None:
            i = self.subject.findData(current)
            if i >= 0:
                self.subject.setCurrentIndex(i)

    def add_subject(self):
        name, ok = QInputDialog.getText(self, "Mata kuliah baru", "Nama:")
        if ok and name.strip():
            try:
                s = self.api.add_subject(name.strip())
            except ApiError as e:
                QMessageBox.warning(self, "Error", str(e))
                return
            self.refresh()
            self.subject.setCurrentIndex(self.subject.findData(s["id"]))

    # timer
    def _fmt(self):
        m, s = divmod(self.remaining, 60)
        self.clock.setText(f"{m:02d}:{s:02d}")

    def reset(self):
        self.ticker.stop()
        self.running = False
        self.phase = "fokus"
        self.remaining = self.focus_min.value() * 60
        self.phase_lbl.setText("FOKUS")
        self.start_btn.setText("Mulai")
        self._fmt()

    def toggle(self):
        if self.running:
            self.ticker.stop()
            self.running = False
            self.start_btn.setText("Lanjut")
            return
        if self.phase == "fokus" and self.subject.currentData() is None:
            QMessageBox.information(self, "Pilih mata kuliah", "Tambah/pilih mata kuliah dulu.")
            return
        self.running = True
        self.ticker.start()
        self.start_btn.setText("Jeda")

    def tick(self):
        self.remaining -= 1
        self._fmt()
        if self.remaining <= 0:
            self.finish_phase()

    def finish_phase(self):
        self.ticker.stop()
        self.running = False
        if self.phase == "fokus":
            minutes = self.focus_min.value()
            try:
                self.api.add_session(self.subject.currentData(), minutes)
                self.session_count += 1
                self.today.setText(f"Sesi selesai di jendela ini: {self.session_count}")
            except ApiError as e:
                QMessageBox.warning(self, "Gagal menyimpan sesi", str(e))
            self.phase = "istirahat"
            self.remaining = self.break_min.value() * 60
            self.phase_lbl.setText("ISTIRAHAT")
        else:
            self.phase = "fokus"
            self.remaining = self.focus_min.value() * 60
            self.phase_lbl.setText("FOKUS")
        self.start_btn.setText("Mulai")
        self._fmt()
        QMessageBox.information(self, "Pomodoro", f"Fase berikutnya: {self.phase}")
