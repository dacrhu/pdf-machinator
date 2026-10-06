# PyInstaller spec – használat (a repo gyökeréből): pyinstaller packaging/pdfmachinator.spec
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
APP = "PDF Machinator"
ICON = {"win32": "icon.ico", "darwin": "icon.icns"}.get(sys.platform, "icon.png")

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT / "src")],
    datas=[(str(ROOT / "src" / "pdfmachinator" / "assets" / "icon.png"), "pdfmachinator/assets")],
    excludes=["tkinter", "PySide6.QtNetwork", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtWebEngineCore",
              "PySide6.QtMultimedia", "PySide6.Qt3DCore", "PySide6.QtCharts", "PySide6.QtSql"],
)
pyz = PYZ(a.pure)
icon = str(ROOT / "assets" / ICON)

if sys.platform == "win32":
    # egyetlen .exe
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name=APP, icon=icon, console=False, upx=False)
else:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="pdfmachinator", console=False, upx=False)
    coll = COLLECT(exe, a.binaries, a.datas, name="pdfmachinator", upx=False)
    if sys.platform == "darwin":
        app = BUNDLE(coll, name=f"{APP}.app", icon=icon, bundle_identifier="hu.dacr.pdfmachinator",
                     info_plist={"CFBundleShortVersionString": "1.0.0", "CFBundleName": APP,
                                 "NSHighResolutionCapable": True,
                                 "CFBundleDocumentTypes": [{"CFBundleTypeName": "PDF", "CFBundleTypeRole": "Editor",
                                                            "LSItemContentTypes": ["com.adobe.pdf"]}]})
