import multiprocessing
import sys

from PyQt5.QtWidgets import QApplication

try:
    from .gui import PUBGISMainWindow
except ImportError:
    from pubgis.gui import PUBGISMainWindow

if __name__ == "__main__":
    multiprocessing.freeze_support()
    APP = QApplication(sys.argv)
    WIN = PUBGISMainWindow()
    sys.exit(APP.exec_())
