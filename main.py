"""
Forge 3D — direct launcher (development / already-installed shortcut).

For normal use, run  run.bat  instead — it shows the loading screen and
installs any missing packages automatically.

Use this file only when all packages are already present.
"""
import sys

# Qt 6 already sets per-monitor DPI awareness on Windows — no ctypes needed.
# AA_UseHighDpiPixmaps is deprecated in Qt 6, skip it too.

from PySide6.QtWidgets import QApplication
from PySide6.QtCore    import Qt
from PySide6.QtGui     import QPalette, QColor, QFont

from window import MainWindow, DARK_QSS


def _dark_palette() -> QPalette:
    p = QPalette()
    _c = QColor
    p.setColor(QPalette.Window,          _c(0x08, 0x08, 0x0e))
    p.setColor(QPalette.WindowText,      _c(0xe8, 0xe8, 0xed))
    p.setColor(QPalette.Base,            _c(0x12, 0x12, 0x1c))
    p.setColor(QPalette.AlternateBase,   _c(0x1c, 0x1c, 0x2a))
    p.setColor(QPalette.ToolTipBase,     _c(0x1c, 0x1c, 0x2a))
    p.setColor(QPalette.ToolTipText,     _c(0xe8, 0xe8, 0xed))
    p.setColor(QPalette.Text,            _c(0xe8, 0xe8, 0xed))
    p.setColor(QPalette.Button,          _c(0x1c, 0x1c, 0x2a))
    p.setColor(QPalette.ButtonText,      _c(0xe8, 0xe8, 0xed))
    p.setColor(QPalette.BrightText,      _c(255, 255, 255))
    p.setColor(QPalette.Link,            _c(0x2e, 0x7c, 0xff))
    p.setColor(QPalette.Highlight,       _c(0x2e, 0x7c, 0xff))
    p.setColor(QPalette.HighlightedText, _c(255, 255, 255))
    p.setColor(QPalette.PlaceholderText, _c(0x88, 0x88, 0x99))
    p.setColor(QPalette.Mid,             _c(0x28, 0x28, 0x38))
    p.setColor(QPalette.Dark,            _c(0x08, 0x08, 0x0e))
    p.setColor(QPalette.Shadow,          _c(0, 0, 0, 180))
    for role in (QPalette.WindowText, QPalette.Text,
                 QPalette.ButtonText, QPalette.Highlight):
        p.setColor(QPalette.Disabled, role,
                   p.color(QPalette.PlaceholderText))
    return p


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Forge 3D")
    app.setOrganizationName("ForgeAI")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")
    app.setPalette(_dark_palette())
    app.setStyleSheet(DARK_QSS)

    font = QFont()
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    for face in ("SF Pro Display", "Segoe UI", "Helvetica Neue", "Arial"):
        font.setFamily(face)
        if font.exactMatch():
            break
    font.setPointSize(10)
    app.setFont(font)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
