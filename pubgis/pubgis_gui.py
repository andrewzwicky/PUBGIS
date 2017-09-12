import os
import sys
import time

import cv2
from PyQt5 import QtCore, uic
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsScene, QColorDialog

from pubgis.pubgis_color import Color, ColorSpace, ColorScaling
from pubgis_match import PUBGISMatch, DEFAULT_PATH_COLOR, VideoIterator


class PUBGISWorkerThread(QThread):
    percent_update = QtCore.pyqtSignal(int)
    percent_max_update = QtCore.pyqtSignal(int)
    minimap_update = QtCore.pyqtSignal(QImage)

    def __init__(self,
                 parent,
                 video_file,
                 step_interval,
                 landing_time_text,
                 death_time_text,
                 output_file,
                 path_color):
        super(PUBGISWorkerThread, self).__init__(parent)
        self.video_file = video_file
        self.step_interval = step_interval
        self.landing_time = self.parse_time(landing_time_text)
        self.death_time = self.parse_time(death_time_text)
        if self.death_time == 0:
            self.death_time = None
        self.output_file = output_file
        self.path_color = path_color

    @staticmethod
    def parse_time(input_string):
        ret = time.strptime(input_string, '%M:%S')
        int_val = ret.tm_min * 60 + ret.tm_sec
        return int_val

    @staticmethod
    def img_to_qimg(img):
        img2 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        height, width, _ = img2.shape
        bytes_per_line = 3 * width
        return QImage(img2.data, width, height, bytes_per_line, QImage.Format_RGB888)

    def run(self):
        self.percent_max_update.emit(0)
        video = VideoIterator(video_file=self.video_file,
                              landing_time=self.landing_time,
                              death_time=self.death_time,
                              step_interval=self.step_interval)

        match = PUBGISMatch(minimap_iterator=video,
                            output_file=self.output_file,
                            path_color=self.path_color)

        self.minimap_update.emit(self.img_to_qimg(match.full_map))

        percent_init = False

        for percent, progress_minimap in match.process_match():
            if not percent_init:
                self.percent_max_update.emit(100)
                percent_init = True
            self.percent_update.emit(percent)
            self.minimap_update.emit(self.img_to_qimg(progress_minimap))

        self.percent_update.emit(100)
        match.create_output()


class PUBGISMainWindow(QMainWindow):
    changed_percent = QtCore.pyqtSignal(int)
    update_minimap = QtCore.pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "pubgis_gui.ui"), self)
        self.color_select_button.released.connect(self.select_background_color)

        self.process_button.released.connect(self.process_match)
        self.video_file_browse_button.clicked.connect(self._select_video_file)
        self.output_file_browse_button.clicked.connect(self._select_output_file)

        # TODO: better duration input
        self.map_creation_view.setScene(QGraphicsScene())
        self.map_pixmap = self.map_creation_view.scene().addPixmap(QPixmap())

        self.path_color = DEFAULT_PATH_COLOR
        self.update_path_color_preview()

        # TODO: remove this once done testing
        self.video_file_edit.setText(r"E:\Movies\OBS\2017-09-07_20-16-43.mp4")
        self.landing_time_edit.setText(r"00:00")
        self.death_time_edit.setText(r"00:00")

        self.show()

    def _select_video_file(self):
        fname, _ = QFileDialog.getOpenFileName(directory=os.path.expanduser('~'),
                                               filter="Videos (*.mp4)")
        self.video_file_edit.setText(fname)

    def _select_output_file(self):
        fname, _ = QFileDialog.getSaveFileName(directory=os.path.expanduser('~'),
                                               filter="Images (*.jpg)")
        self.output_file_edit.setText(fname)

    def select_background_color(self):
        color_dialog = QColorDialog(QColor(*self.path_color.get_with_alpha()))
        *picker_rgb, alpha = color_dialog.getColor(options=QColorDialog.ShowAlphaChannel).getRgb()
        self.path_color = Color(picker_rgb, scaling=ColorScaling.UINT8, alpha=alpha)
        self.update_path_color_preview()

    def update_path_color_preview(self):
        style = "background-color:rgb({},{},{})".format(*self.path_color.get(space=ColorSpace.RGB))
        self.path_color_preview.setStyleSheet(style)

    def update_map_preview(self, qimg):
        self.map_pixmap.setPixmap(QPixmap.fromImage(qimg))
        self.map_creation_view.fitInView(self.map_creation_view.scene().itemsBoundingRect())
        self.map_creation_view.update()
        self.map_creation_view.repaint()

    def process_match(self):
        if self.video_file_edit.text() != "":
            match_thread = PUBGISWorkerThread(self,
                                              self.video_file_edit.text(),
                                              int(self.time_step_combo.currentText()),
                                              self.landing_time_edit.text(),
                                              self.death_time_edit.text(),
                                              self.output_file_edit.text(),
                                              self.path_color)

            match_thread.percent_update.connect(self.progress_bar.setValue)
            match_thread.percent_max_update.connect(self.progress_bar.setMaximum)
            match_thread.minimap_update.connect(self.update_map_preview)
            match_thread.start()


if __name__ == "__main__":
    APP = QApplication(sys.argv)
    WIN = PUBGISMainWindow()

    sys.exit(APP.exec_())
