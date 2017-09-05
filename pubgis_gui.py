#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import time

import cv2
from PyQt5 import QtCore, uic
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QPixmap, QColor, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, \
    QGraphicsScene, QColorDialog

from pubgis import PUBGISMatch


class PUBGISApplication(QApplication):
    def __init__(self, args):
        super().__init__(args)


class PUBGISWorkerThread(QThread):
    percent_update = QtCore.pyqtSignal(int)
    minimap_update = QtCore.pyqtSignal(QImage)

    def __init__(self, parent):
        super(PUBGISWorkerThread, self).__init__(parent)

    @staticmethod
    def parse_time_optional_minutes(input_string):
        ret = time.strptime(input_string, '%M:%S')
        int_val = ret.tm_min * 60 + ret.tm_sec
        return int_val

    # noinspection PyAttributeOutsideInit
    def start_with_params(self, video_file, time_step_text, start_delay_text, death_time_text, output_file, path_color):
        self.video_file = video_file
        self.time_step = time_step_text
        self.start_delay = start_delay_text
        self.death_time = death_time_text
        self.output_file = output_file
        self.path_color = path_color
        self.start()

    def run(self):
        time_args = dict()
        if self.time_step != "":
            time_args["step_time"] = self.parse_time_optional_minutes(self.time_step)

        if self.start_delay != "":
            time_args["start_delay"] = self.parse_time_optional_minutes(self.start_delay)

        if self.death_time != "":
            time_args["death_time"] = self.parse_time_optional_minutes(self.death_time)

        match = PUBGISMatch(video_file=self.video_file,
                            output_file=self.output_file,
                            debug=False,
                            path_color=(self.path_color.blue(),
                                        self.path_color.green(),
                                        self.path_color.red()),
                            **time_args)

        for percent, progress_minimap in match.process_match():
            self.percent_update.emit(percent)
            img2 = cv2.cvtColor(progress_minimap, cv2.COLOR_BGR2RGB)
            height, width, channel = img2.shape
            bytes_per_line = 3 * width
            qimg = QImage(img2.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.minimap_update.emit(qimg)

        match.create_output()


class PUBGISMainWindow(QMainWindow):
    changed_percent = QtCore.pyqtSignal(int)
    update_minimap = QtCore.pyqtSignal(QImage)

    def __init__(self):
        # noinspection PyArgumentList
        super().__init__()
        uic.loadUi('pubgis_gui.ui', self)
        self.color_select_button.released.connect(self.select_background_color)
        self.path_color = QColor(0, 255, 0, 0)
        self.update_path_color_preview()
        self.process_button.released.connect(self.process_match)
        self.video_file_browse_button.clicked.connect(self._select_video_file)
        self.output_file_browse_button.clicked.connect(self._select_output_file)

        self.thread = PUBGISWorkerThread(self)

        self.thread.percent_update.connect(self.progress_bar.setValue)
        self.thread.minimap_update.connect(self.update_map_preview)
        self.cancel_button.released.connect(self.thread.exit)

        self.map_creation_view.setScene(QGraphicsScene())
        self.map_pixmap = self.map_creation_view.scene().addPixmap(QPixmap())
        self.show()

    def _select_video_file(self):
        # noinspection PyArgumentList,PyArgumentList
        fname, _ = QFileDialog.getOpenFileName(directory=os.path.expanduser('~'), filter="Videos (*.mp4)")
        self.video_file_edit.setText(fname)

    def _select_output_file(self):
        # noinspection PyArgumentList,PyArgumentList
        fname, _ = QFileDialog.getOpenFileName(directory=os.path.expanduser('~'), filter="Images (*.jpg)")
        self.output_file_edit.setText(fname)

    def select_background_color(self):
        color_dialog = QColorDialog()
        # noinspection PyArgumentList
        self.path_color = color_dialog.getColor()
        self.update_path_color_preview()

    def update_path_color_preview(self):
        p = self.path_color_preview.palette()
        p.setColor(self.path_color_preview.backgroundRole(), self.path_color)
        self.path_color_preview.setPalette(p)

    def update_map_preview(self, qimg):
        # todo: mutex?
        # noinspection PyArgumentList,PyArgumentList
        self.map_pixmap.setPixmap(QPixmap.fromImage(qimg))
        self.map_creation_view.fitInView(self.map_creation_view.scene().itemsBoundingRect())
        self.map_creation_view.update()
        self.map_creation_view.repaint()

    def process_match(self):
        if self.video_file_edit.text() != "":
            self.thread.start_with_params(self.video_file_edit.text(),
                                          self.time_step_edit.text(),
                                          self.landing_time_edit.text(),
                                          self.death_time_edit.text(),
                                          self.output_file_edit.text(),
                                          self.path_color)


if __name__ == "__main__":
    app = PUBGISApplication(sys.argv)
    win = PUBGISMainWindow()

    sys.exit(app.exec_())
