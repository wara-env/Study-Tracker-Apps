import json

from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (
    QComboBox, QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem,
    QGraphicsTextItem, QGraphicsView, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)

from api import ApiError

KINDS = {"teori": "#dbeafe", "rumus": "#fef3c7", "penerapan": "#dcfce7"}


class NodeItem(QGraphicsRectItem):
    def __init__(self, node_id, text, kind, x, y):
        super().__init__()
        self.node_id, self.kind, self.edges = node_id, kind, []
        self.label = QGraphicsTextItem(self)
        self.label.setDefaultTextColor(QColor("#111"))
        self.label.setTextWidth(160)
        self.setFlags(
            QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setBrush(QBrush(QColor(KINDS.get(kind, "#eee"))))
        self.setPen(QPen(QColor("#6366f1"), 1.5))
        self.set_text(text)
        self.setPos(x, y)

    def set_text(self, text):
        self.text = text
        self.label.setPlainText(text)
        r = self.label.boundingRect()
        self.setRect(0, 0, max(r.width(), 80) + 0, r.height() + 4)

    def center(self):
        return self.sceneBoundingRect().center()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for e in self.edges:
                e.update_position()
        return super().itemChange(change, value)


class EdgeItem(QGraphicsRectItem):
    """Garis berpanah antar node + label hubungan."""

    def __init__(self, a, b, label=""):
        super().__init__()
        self.a, self.b, self.text = a, b, label
        self.line = QLineF()
        self.setZValue(-1)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.caption = QGraphicsSimpleTextItem(label, self)
        self.caption.setBrush(QBrush(QColor("#475569")))
        a.edges.append(self)
        b.edges.append(self)
        self.update_position()

    def update_position(self):
        self.prepareGeometryChange()
        self.line = QLineF(self.a.center(), self.b.center())
        self.caption.setPos(self.line.pointAt(0.5))

    def _arrow_tip(self):
        rect = self.b.sceneBoundingRect()
        corners = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
        for i in range(4):
            edge = QLineF(corners[i], corners[(i + 1) % 4])
            kind, point = self.line.intersects(edge)
            if kind == QLineF.BoundedIntersection:
                return point
        return self.line.p2()

    def boundingRect(self):
        return QRectF(self.line.p1(), self.line.p2()).normalized().adjusted(-40, -40, 40, 40)

    def shape(self):
        from PySide6.QtGui import QPainterPath, QPainterPathStroker

        p = QPainterPath(self.line.p1())
        p.lineTo(self.line.p2())
        s = QPainterPathStroker()
        s.setWidth(10)
        return s.createStroke(p)

    def paint(self, painter, option, widget=None):
        if self.line.length() < 1:
            return
        color = QColor("#dc2626") if self.isSelected() else QColor("#475569")
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        tip = self._arrow_tip()
        painter.drawLine(QLineF(self.line.p1(), tip))
        back = QLineF(tip, self.line.p1())
        back.setLength(12)
        left, right = QLineF(back), QLineF(back)
        left.setAngle(back.angle() + 25)
        right.setAngle(back.angle() - 25)
        painter.drawPolygon(QPolygonF([tip, left.p2(), right.p2()]))

    def detach(self):
        for n in (self.a, self.b):
            if self in n.edges:
                n.edges.remove(self)


class MapView(QGraphicsView):
    def __init__(self, scene, on_double_click):
        super().__init__(scene)
        self.on_double_click = on_double_click
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            f = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
            self.scale(f, f)
        else:
            super().wheelEvent(e)

    def mouseDoubleClickEvent(self, e):
        item = self.itemAt(e.pos())
        while item is not None and not isinstance(item, NodeItem):
            item = item.parentItem()
        if item is not None:
            self.on_double_click(item)
        else:
            super().mouseDoubleClickEvent(e)


class ConceptMapTab(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.current_id = None
        self.nodes, self.edges, self.next_id = {}, [], 1

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        self.view = MapView(self.scene, self.edit_node)

        self.map_combo = QComboBox()
        self.map_combo.setMinimumWidth(180)
        self.map_combo.activated.connect(self.on_pick)
        self.kind = QComboBox()
        self.kind.addItems(list(KINDS))

        def btn(text, fn):
            b = QPushButton(text)
            b.clicked.connect(fn)
            return b

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Peta:"))
        bar.addWidget(self.map_combo)
        bar.addWidget(btn("Baru", self.new_map))
        bar.addWidget(btn("Hapus peta", self.delete_map))
        bar.addSpacing(16)
        bar.addWidget(self.kind)
        bar.addWidget(btn("+ Node", self.add_node))
        bar.addWidget(btn("Hubungkan 2 node", self.connect_selected))
        bar.addWidget(btn("Hapus terpilih", self.delete_selected))
        bar.addStretch(1)
        bar.addWidget(btn("Simpan", self.save))

        hint = QLabel("Dobel-klik node = edit teks · pilih 2 node (Ctrl+klik) lalu Hubungkan · Ctrl+scroll = zoom")
        hint.setObjectName("hint")

        lay = QVBoxLayout(self)
        lay.addLayout(bar)
        lay.addWidget(hint)
        lay.addWidget(self.view, 1)

    def _err(self, e):
        QMessageBox.warning(self, "Error", str(e))

    # ---- daftar peta ----
    def refresh(self):
        try:
            maps = self.api.maps()
        except ApiError as e:
            return self._err(e)
        self.map_combo.clear()
        for m in maps:
            self.map_combo.addItem(m["title"], m["id"])
        if maps:
            i = self.map_combo.findData(self.current_id)
            self.map_combo.setCurrentIndex(max(i, 0))
            self.load(self.map_combo.currentData())
        else:
            self.current_id = None
            self._clear()

    def on_pick(self, _idx):
        self.save(quiet=True)
        self.load(self.map_combo.currentData())

    def new_map(self):
        title, ok = QInputDialog.getText(self, "Peta konsep baru", "Judul (mis. Hukum Ohm):")
        if not (ok and title.strip()):
            return
        self.save(quiet=True)
        try:
            m = self.api.add_map(title.strip())
        except ApiError as e:
            return self._err(e)
        self.current_id = m["id"]
        self.refresh()

    def delete_map(self):
        if self.current_id is None:
            return
        if QMessageBox.question(self, "Hapus peta", "Hapus peta ini permanen?") != QMessageBox.Yes:
            return
        try:
            self.api.delete_map(self.current_id)
        except ApiError as e:
            return self._err(e)
        self.current_id = None
        self.refresh()

    # ---- scene ----
    def _clear(self):
        self.scene.clear()
        self.nodes, self.edges, self.next_id = {}, [], 1

    def load(self, mid):
        if mid is None:
            return
        try:
            data = json.loads(self.api.get_map(mid)["data"])
        except (ApiError, ValueError) as e:
            return self._err(e)
        self.current_id = mid
        self._clear()
        for n in data["nodes"]:
            self._make_node(n["id"], n["text"], n["kind"], n["x"], n["y"])
        for e in data["edges"]:
            a, b = self.nodes.get(e["from"]), self.nodes.get(e["to"])
            if a and b:
                self._make_edge(a, b, e.get("label", ""))
        self.next_id = max(self.nodes, default=0) + 1

    def _make_node(self, nid, text, kind, x, y):
        n = NodeItem(nid, text, kind, x, y)
        self.scene.addItem(n)
        self.nodes[nid] = n
        return n

    def _make_edge(self, a, b, label):
        e = EdgeItem(a, b, label)
        self.scene.addItem(e)
        self.edges.append(e)
        return e

    def serialize(self):
        return {
            "nodes": [
                {"id": n.node_id, "text": n.text, "kind": n.kind, "x": n.pos().x(), "y": n.pos().y()}
                for n in self.nodes.values()
            ],
            "edges": [{"from": e.a.node_id, "to": e.b.node_id, "label": e.text} for e in self.edges],
        }

    def save(self, quiet=False):
        if self.current_id is None:
            return
        try:
            self.api.save_map(self.current_id, self.serialize())
        except ApiError as e:
            if not quiet:
                self._err(e)

    # ---- aksi ----
    def add_node(self):
        if self.current_id is None:
            return QMessageBox.information(self, "Peta", "Buat peta baru dulu.")
        text, ok = QInputDialog.getText(self, "Node baru", f"Teks ({self.kind.currentText()}):")
        if not (ok and text.strip()):
            return
        c = self.view.mapToScene(self.view.viewport().rect().center())
        off = 30 * (len(self.nodes) % 8)
        self._make_node(self.next_id, text.strip(), self.kind.currentText(), c.x() - 60 + off, c.y() - 20 + off)
        self.next_id += 1

    def edit_node(self, node):
        text, ok = QInputDialog.getMultiLineText(self, "Edit node", "Teks:", node.text)
        if ok and text.strip():
            node.set_text(text.strip())
            for e in node.edges:
                e.update_position()

    def connect_selected(self):
        sel = [i for i in self.scene.selectedItems() if isinstance(i, NodeItem)]
        if len(sel) != 2:
            return QMessageBox.information(self, "Hubungkan", "Pilih tepat 2 node (Ctrl+klik).")
        label, ok = QInputDialog.getText(self, "Hubungan", "Label (mis. 'dipakai di', 'diturunkan dari'):")
        if ok:
            # panah dari node yang dipilih lebih dulu (kiri) ke yang lain
            a, b = sorted(sel, key=lambda n: n.pos().x())
            self._make_edge(a, b, label.strip())

    def delete_selected(self):
        for item in self.scene.selectedItems():
            if isinstance(item, EdgeItem):
                self._remove_edge(item)
        for item in self.scene.selectedItems():
            if isinstance(item, NodeItem):
                for e in list(item.edges):
                    self._remove_edge(e)
                self.nodes.pop(item.node_id, None)
                self.scene.removeItem(item)

    def _remove_edge(self, e):
        e.detach()
        if e in self.edges:
            self.edges.remove(e)
        if e.scene():
            self.scene.removeItem(e)
