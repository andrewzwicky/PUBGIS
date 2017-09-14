import sys

from PyQt5.QtWidgets import QApplication

from .gui import PUBGISMainWindow

if __name__ == "__main__":
    APP = QApplication(sys.argv)
    WIN = PUBGISMainWindow()

    sys.exit(APP.exec_())
