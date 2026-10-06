import sys

from PySide6.QtWidgets import QApplication

from PySide6.QtCore import QLibraryInfo, QTranslator

from .i18n import LANG
from .mainwindow import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Machinator")
    # a Qt saját szövegei (színválasztó, Mentés/Mégse gombok, fájlablak) is a nyelvünkön
    qt_tr = QTranslator()
    if LANG != "en" and qt_tr.load(f"qtbase_{LANG}", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)):
        app.installTranslator(qt_tr)
    w = MainWindow(sys.argv[1] if len(sys.argv) > 1 else None)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
