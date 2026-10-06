"""assets/icon.svg -> icon.png (1024), icon.ico (Windows), icon.icns (macOS),
és a csomagba másolt ablakikon. Futtatás: python tools/make_icons.py (Pillow + PySide6 kell)."""
import io
import shutil
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parent.parent
app = QGuiApplication([])  # noqa: F841 (a Qt képkezeléshez kell)


def render(size):
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(0)
    p = QPainter(img)
    QSvgRenderer(str(ROOT / "assets" / "icon.svg")).render(p)
    p.end()
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return Image.open(io.BytesIO(bytes(buf.data()))).convert("RGBA")


big = render(1024)
big.save(ROOT / "assets" / "icon.png")
big.save(ROOT / "assets" / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
big.save(ROOT / "assets" / "icon.icns")
(ROOT / "src" / "pdfmachinator" / "assets").mkdir(exist_ok=True)
render(256).save(ROOT / "src" / "pdfmachinator" / "assets" / "icon.png")
print("ok")
