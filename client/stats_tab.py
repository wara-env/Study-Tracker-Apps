from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QVBoxLayout, QWidget

from api import ApiError


class StatsTab(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api

        self.range = QComboBox()
        for label, days in (("7 hari", 7), ("30 hari", 30), ("90 hari", 90)):
            self.range.addItem(label, days)
        self.range.currentIndexChanged.connect(self.refresh)
        self.summary = QLabel("")
        self.summary.setStyleSheet("font-size: 14px")

        self.fig = Figure(figsize=(8, 4), tight_layout=True, facecolor="#0f172a")
        self.canvas = Canvas(self.fig)

        top = QHBoxLayout()
        top.addWidget(QLabel("Rentang:"))
        top.addWidget(self.range)
        top.addWidget(self.summary, 1)

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.canvas, 1)

    def refresh(self):
        try:
            s = self.api.stats(self.range.currentData())
        except ApiError as e:
            QMessageBox.warning(self, "Error", str(e))
            return
        h, m = divmod(s["total_minutes"], 60)
        self.summary.setText(f"Total: {h} jam {m} menit    |    Streak: {s['streak']} hari")

        self.fig.clear()

        def style(ax):
            ax.set_facecolor("#1e293b")
            for sp in ax.spines.values():
                sp.set_color("#334155")
            ax.tick_params(colors="#94a3b8")
            ax.xaxis.label.set_color("#94a3b8")
            ax.yaxis.label.set_color("#94a3b8")
            ax.title.set_color("#e2e8f0")
        ax1 = self.fig.add_subplot(1, 2, 1)
        days = list(s["daily"].keys())
        ax1.bar(range(len(days)), list(s["daily"].values()), color="#6366f1")
        step = max(1, len(days) // 7)
        ax1.set_xticks(range(0, len(days), step))
        ax1.set_xticklabels([d[5:] for d in days[::step]], rotation=45, ha="right")
        ax1.set_ylabel("Menit")
        ax1.set_title("Belajar per hari")
        style(ax1)

        ax2 = self.fig.add_subplot(1, 2, 2)
        subj = s["by_subject"]
        if subj:
            names = list(subj.keys())
            ax2.barh(names, list(subj.values()), color="#10b981")
            ax2.invert_yaxis()
        else:
            ax2.text(0.5, 0.5, "Belum ada data", ha="center", va="center", transform=ax2.transAxes, color="#94a3b8")
            ax2.set_xticks([])
            ax2.set_yticks([])
        ax2.set_xlabel("Menit")
        ax2.set_title("Per mata kuliah")
        style(ax2)
        self.canvas.draw_idle()
