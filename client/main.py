import os
import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from api import Api
from conceptmap_tab import ConceptMapTab
from login import LoginDialog
from stats_tab import StatsTab
from tasks_tab import TasksTab
from theme import QSS
from timer_tab import TimerTab


class MainWindow(QMainWindow):
    def __init__(self, api):
        super().__init__()
        self.setWindowTitle("Study Tracker")
        self.resize(1000, 680)

        self.timer = TimerTab(api)
        self.tasks = TasksTab(api)
        self.stats = StatsTab(api)
        self.cmap = ConceptMapTab(api)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.timer, "Timer")
        self.tabs.addTab(self.tasks, "Tugas")
        self.tabs.addTab(self.stats, "Statistik")
        self.tabs.addTab(self.cmap, "Concept Map")
        self.tabs.currentChanged.connect(self.on_tab)
        self.setCentralWidget(self.tabs)
        self.timer.refresh()

    def on_tab(self, i):
        w = self.tabs.widget(i)
        if w is not self.cmap:
            self.cmap.save(quiet=True)
        w.refresh()

    def closeEvent(self, e):
        self.cmap.save(quiet=True)
        super().closeEvent(e)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(QSS)
    api = Api(os.environ.get("STUDY_API", "http://127.0.0.1:5000"))
    if LoginDialog(api).exec() != LoginDialog.Accepted:
        return 0
    win = MainWindow(api)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
