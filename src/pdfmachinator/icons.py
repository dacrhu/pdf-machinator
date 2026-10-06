"""Vonalas SVG ikonok (24x24, 2px vonal). A színt futásidőben állítjuk,
így a világos/sötét témához igazodnak; nincs külső ikoncsomag-függés."""
from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

PATHS = {
    "open": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "save": '<path d="M5 3h11l4 4v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>'
            '<path d="M7 3v5h8V3"/><rect x="7" y="13" width="10" height="8"/>',
    "undo": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/>',
    "select": '<path d="M5 3l14 7-6 2-2 6z"/>',
    "text": '<path d="M5 7V4h14v3"/><path d="M12 4v13"/><path d="M9 20h6"/><path d="M12 17v3"/>',
    "note": '<path d="M4 4h16v11l-5 5H4z"/><path d="M15 20v-5h5"/><path d="M8 9h8M8 12.5h5"/>',
    "highlight": '<path d="m9 11-6 6v3h9l3-3"/>'
                 '<path d="m22 12-4.6 4.6a2 2 0 0 1-2.8 0l-5.2-5.2a2 2 0 0 1 0-2.8L14 4"/>',
    "circle": '<ellipse cx="12" cy="12" rx="9" ry="6.5" transform="rotate(-20 12 12)"/>',
    "prev": '<path d="M15 6l-6 6 6 6"/>',
    "next": '<path d="M9 6l6 6-6 6"/>',
    "zoom_in": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3M11 8v6M8 11h6"/>',
    "zoom_out": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3M8 11h6"/>',
    "fit": '<path d="M4 5v14M20 5v14M8 12h8M8 12l2.5-2.5M8 12l2.5 2.5M16 12l-2.5-2.5M16 12l-2.5 2.5"/>',
    "bucket": '<path d="m19 11-8-8-8.6 8.6a2 2 0 0 0 0 2.8l5.2 5.2c.8.8 2 .8 2.8 0L19 11z"/>'
              '<path d="m5 2 5 5M2 13h15"/><path d="M22 20a2 2 0 1 1-4 0c0-1.6 2-4 2-4s2 2.4 2 4z"/>',
}


def _render(name, color, size, extra=""):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color.name()}" '
           f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}{extra}</svg>')
    scale = 2  # éles megjelenés HiDPI-n
    pm = QPixmap(size * scale, size * scale)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    QSvgRenderer(QByteArray(svg.encode())).render(p, QRectF(0, 0, size * scale, size * scale))
    p.end()
    pm.setDevicePixelRatio(scale)
    return pm


def make_icon(name, normal: QColor, active: QColor, disabled: QColor, size=22):
    ic = QIcon()
    ic.addPixmap(_render(name, normal, size), QIcon.Mode.Normal, QIcon.State.Off)
    ic.addPixmap(_render(name, active, size), QIcon.Mode.Normal, QIcon.State.On)
    ic.addPixmap(_render(name, disabled, size), QIcon.Mode.Disabled, QIcon.State.Off)
    return ic


def swatch_icon(color: QColor | None, border: QColor, size=22, alpha=1.0, glyph=None):
    """Színminta-ikon (None = nincs szín: áthúzott, kockás)."""
    scale = 2
    pm = QPixmap(size * scale, size * scale)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size * scale
    r = QRectF(s * 0.14, s * 0.14, s * 0.72, s * 0.72)
    p.setPen(Qt.PenStyle.NoPen)
    # kockás alap, hogy az áttetszőség látszódjon
    p.save()
    from PySide6.QtGui import QPainterPath
    path = QPainterPath()
    path.addRoundedRect(r, s * 0.14, s * 0.14)
    p.setClipPath(path)
    cell = s * 0.12
    for i in range(8):
        for j in range(8):
            p.setBrush(QColor("#ffffff") if (i + j) % 2 == 0 else QColor("#c8c8c8"))
            p.drawRect(QRectF(r.x() + i * cell, r.y() + j * cell, cell, cell))
    if color is not None:
        c = QColor(color)
        c.setAlphaF(alpha)
        p.setBrush(c)
        p.drawRect(r)
    p.restore()
    from PySide6.QtGui import QPen
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(border, s * 0.07))
    p.drawRoundedRect(r, s * 0.14, s * 0.14)
    if color is None:
        p.setPen(QPen(QColor("#e53935"), s * 0.08))
        p.drawLine(r.bottomLeft(), r.topRight())
    p.end()
    pm.setDevicePixelRatio(scale)
    return QIcon(pm)
