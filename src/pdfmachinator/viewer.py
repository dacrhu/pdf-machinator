import pymupdf
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QImage, QPen, QPixmap
from PySide6.QtWidgets import QFrame, QGraphicsScene, QGraphicsView

from .i18n import tr


class Viewer(QGraphicsView):
    """Egy oldalt mutat; az egéreseményeket PDF-koordinátákra váltja."""
    drag_done = Signal(object)                 # pdf Rect
    clicked = Signal(object)                   # pdf Point
    zoom_changed = Signal(float)
    wants_drag = False                         # a főablak állítja az eszköz szerint
    drag_shape = "rect"                        # "rect" | "ellipse"

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setBackgroundBrush(Qt.GlobalColor.lightGray)
        self.zoom = 1.5
        self.page = None
        self._start = None
        self._rubber = None
        self.setFrameShape(QFrame.Shape.NoFrame)
        t = self.scene().addText(tr("Nyiss meg egy PDF-et\n(Ctrl+O), vagy húzd ide a fájlt"))
        t.setDefaultTextColor(Qt.GlobalColor.gray)
        f = t.font()
        f.setPointSize(16)
        t.setFont(f)

    def show_page(self, page):
        self.page = page
        self.render_page()

    def render_page(self):
        if self.page is None:
            return
        pix = self.page.get_pixmap(matrix=pymupdf.Matrix(self.zoom, self.zoom), alpha=False, annots=True)
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
        self.scene().clear()
        self._rubber = None
        self.scene().addPixmap(QPixmap.fromImage(img))
        self.scene().setSceneRect(QRectF(0, 0, pix.width, pix.height))

    def set_zoom(self, z):
        self.zoom = max(0.3, min(6.0, z))
        self.render_page()
        self.zoom_changed.emit(self.zoom)

    def fit_width(self):
        if self.page is not None:
            avail = self.viewport().width() - 24
            self.set_zoom(avail / self.page.rect.width)

    def to_pdf(self, sp):
        p = pymupdf.Point(sp.x() / self.zoom, sp.y() / self.zoom)
        return p * self.page.derotation_matrix

    def wheelEvent(self, e):
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.set_zoom(self.zoom * (1.1 if e.angleDelta().y() > 0 else 1 / 1.1))
        else:
            super().wheelEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.page is not None:
            self._start = self.mapToScene(e.position().toPoint())
            return
        super().mousePressEvent(e)

    def _shape_rect(self, a, b, square):
        if square:
            d = max(abs(b.x() - a.x()), abs(b.y() - a.y()))
            b = QPointF(a.x() + (d if b.x() >= a.x() else -d), a.y() + (d if b.y() >= a.y() else -d))
        return QRectF(a, b).normalized()

    def mouseMoveEvent(self, e):
        if self._start is None or not self.wants_drag:
            return super().mouseMoveEvent(e)
        cur = self.mapToScene(e.position().toPoint())
        square = bool(e.modifiers() & Qt.KeyboardModifier.ShiftModifier) and self.drag_shape == "ellipse"
        r = self._shape_rect(self._start, cur, square)
        if self._rubber is not None:
            self.scene().removeItem(self._rubber)
        pen = QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DashLine)
        add = self.scene().addEllipse if self.drag_shape == "ellipse" else self.scene().addRect
        self._rubber = add(r, pen)

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton or self._start is None:
            return super().mouseReleaseEvent(e)
        start, self._start = self._start, None
        end = self.mapToScene(e.position().toPoint())
        if self._rubber is not None:
            self.scene().removeItem(self._rubber)
            self._rubber = None
        if self.wants_drag and (end - start).manhattanLength() > 6:
            shift = bool(e.modifiers() & Qt.KeyboardModifier.ShiftModifier)
            r = self._shape_rect(start, end, shift and self.drag_shape == "ellipse")
            a = self.to_pdf(r.topLeft())
            b = self.to_pdf(r.bottomRight())
            self.drag_done.emit(pymupdf.Rect(a, b).normalize())
        else:
            self.clicked.emit(self.to_pdf(end))
