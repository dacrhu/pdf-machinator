#!/usr/bin/env bash
# PyInstaller onedir (dist/pdfmachinator) -> AppImage. Használat: build-appimage.sh <kimeneti-fájl>
set -euo pipefail
OUT="${1:?kimeneti fájlnév kell}"
cd "$(dirname "$0")/../.."

rm -rf AppDir && mkdir -p AppDir/usr/lib AppDir/usr/share/applications
cp -r dist/pdfmachinator AppDir/usr/lib/pdfmachinator
cat > AppDir/AppRun <<'RUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/pdfmachinator/pdfmachinator" "$@"
RUN
chmod +x AppDir/AppRun
cp packaging/linux/hu.dacr.pdfmachinator.desktop AppDir/
cp packaging/linux/hu.dacr.pdfmachinator.desktop AppDir/usr/share/applications/
cp src/pdfmachinator/assets/icon.png AppDir/pdfmachinator.png

if [ ! -x appimagetool ]; then
  curl -fsSL -o appimagetool \
    https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
  chmod +x appimagetool
fi
# FUSE nélküli (CI) környezetben is fut
ARCH=x86_64 ./appimagetool --appimage-extract-and-run AppDir "$OUT"
