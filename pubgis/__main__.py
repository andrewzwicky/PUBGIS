import multiprocessing
import sys

from PyQt5.QtWidgets import QApplication

try:
    from .gui import PUBGISMainWindow
except ImportError:
    from pubgis.gui import PUBGISMainWindow

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = QApplication(sys.argv)
    win = PUBGISMainWindow()
    sys.exit(app.exec_())
