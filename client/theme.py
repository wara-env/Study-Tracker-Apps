"""Tema gelap-modern untuk seluruh app (Qt Style Sheet)."""

BG = "#0f172a"        # latar utama
PANEL = "#1e293b"    # kartu / input
BORDER = "#334155"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#6366f1"   # indigo
ACCENT_HOVER = "#818cf8"
GREEN = "#10b981"
RED = "#ef4444"

QSS = f"""
* {{ font-family: "Segoe UI", "Inter", sans-serif; font-size: 13px; color: {TEXT}; }}
QMainWindow, QDialog, QWidget {{ background: {BG}; }}

QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 10px; background: {BG}; top: -1px; }}
QTabBar::tab {{
    background: transparent; color: {MUTED}; padding: 10px 22px; margin-right: 4px;
    border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: 600;
}}
QTabBar::tab:selected {{ background: {PANEL}; color: white; border-bottom: 3px solid {ACCENT}; }}
QTabBar::tab:hover:!selected {{ color: {TEXT}; background: #172033; }}

QPushButton {{
    background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 16px; font-weight: 600;
}}
QPushButton:hover {{ border-color: {ACCENT}; background: #26344d; }}
QPushButton:pressed {{ background: {ACCENT}; }}
QPushButton:default, QPushButton#primary {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}
QPushButton:default:hover, QPushButton#primary:hover {{ background: {ACCENT_HOVER}; }}

QLineEdit, QSpinBox, QComboBox, QDateTimeEdit, QPlainTextEdit {{
    background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px; padding: 7px 10px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDateTimeEdit:focus {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{ background: {PANEL}; border: 1px solid {BORDER}; selection-background-color: {ACCENT}; }}

QListWidget {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px; outline: 0; }}
QListWidget::item {{ padding: 10px 8px; border-radius: 6px; }}
QListWidget::item:hover {{ background: #26344d; }}
QListWidget::item:selected {{ background: {ACCENT}; color: white; }}

QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 1px solid {BORDER}; background: {PANEL}; }}
QCheckBox::indicator:checked {{ background: {GREEN}; border-color: {GREEN}; }}

QGraphicsView {{ background: #0b1220; border: 1px solid {BORDER}; border-radius: 10px; }}
QLabel#clock {{ font-size: 84px; font-weight: 700; color: white; }}
QLabel#phase {{ font-size: 15px; font-weight: 700; letter-spacing: 2px; color: {ACCENT_HOVER}; }}
QLabel#hint {{ color: {MUTED}; }}
QLabel#error {{ color: {RED}; }}
QMessageBox {{ background: {BG}; }}
"""
