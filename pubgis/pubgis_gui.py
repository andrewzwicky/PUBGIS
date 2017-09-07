#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import sys
import time

import cv2
import matplotlib.colors as mpl_colors
from PyQt5 import QtCore, uic
from PyQt5.QtCore import QThread
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QGraphicsScene, QColorDialog

from pubgis_color import Color, ColorSpace, ColorScaling
from pubgis_match import PUBGISMatch, DEFAULT_PATH_COLOR, DEFAULT_START_DELAY


class PUBGISApplication(QApplication):
    def __init__(self, args):
        super().__init__(args)


class PUBGISWorkerThread(QThread):
    percent_update = QtCore.pyqtSignal(int)
    minimap_update = QtCore.pyqtSignal(QImage)

    def __init__(self, parent):
        super(PUBGISWorkerThread, self).__init__(parent)

    @staticmethod
    def parse_time(input_string):
        ret = time.strptime(input_string, '%M:%S')
        int_val = ret.tm_min * 60 + ret.tm_sec
        return int_val

    # noinspection PyAttributeOutsideInit
    def start_with_params(self, video_file, time_step, start_delay_text, death_time_text, output_file, path_color):
        self.video_file = video_file
        self.time_step = time_step
        self.start_delay = DEFAULT_START_DELAY if start_delay_text == "" else self.parse_time(start_delay_text)
        self.death_time = None if death_time_text == "" else self.parse_time(death_time_text)
        self.output_file = output_file
        self.path_color = path_color
        self.start()

    def run(self):
        match = PUBGISMatch(video_file=self.video_file,
                            output_file=self.output_file,
                            path_color=self.path_color,
                            start_delay=self.start_delay,
                            death_time=self.death_time,
                            step_time=self.time_step)

        for percent, progress_minimap in match.process_match():
            self.percent_update.emit(percent)
            img2 = cv2.cvtColor(progress_minimap, cv2.COLOR_BGR2RGB)
            height, width, channel = img2.shape
            bytes_per_line = 3 * width
            qimg = QImage(img2.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.minimap_update.emit(qimg)

        self.percent_update.emit(100)
        match.create_output()


class PUBGISMainWindow(QMainWindow):
    changed_percent = QtCore.pyqtSignal(int)
    update_minimap = QtCore.pyqtSignal(QImage)

    def __init__(self):
        # noinspection PyArgumentList
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "pubgis_gui.ui"), self)
        self.color_select_button.released.connect(self.select_background_color)

        self.process_button.released.connect(self.process_match)
        self.video_file_browse_button.clicked.connect(self._select_video_file)
        self.output_file_browse_button.clicked.connect(self._select_output_file)

        # TODO: cancel button
        self.thread = PUBGISWorkerThread(self)

        self.thread.percent_update.connect(self.progress_bar.setValue)
        self.thread.minimap_update.connect(self.update_map_preview)

        # TODO: better duration input
        self.map_creation_view.setScene(QGraphicsScene())
        self.map_pixmap = self.map_creation_view.scene().addPixmap(QPixmap())

        self.path_color = DEFAULT_PATH_COLOR
        self.update_path_color_preview()

        self.video_file_edit.setText(r"E:\Movies\OBS\squads_dinner_mike_pat.mp4")

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
        *picker_rgb, a = color_dialog.getColor().getRgb()
        self.path_color = Color(*picker_rgb, scaling=ColorScaling.UINT8)
        self.update_path_color_preview()

    def update_path_color_preview(self):
        style = "background-color : rgb({},{},{})".format(*self.path_color.get(space=ColorSpace.RGB))
        self.path_color_preview.setStyleSheet(style)

    def update_map_preview(self, qimg):
        # todo: mutex?
        # noinspection PyArgumentList,PyArgumentList
        self.map_pixmap.setPixmap(QPixmap.fromImage(qimg))
        self.map_creation_view.fitInView(self.map_creation_view.scene().itemsBoundingRect())
        self.map_creation_view.update()
        self.map_creation_view.repaint()

    def process_match(self):
        # TODO: progress bar while map is loading?
        if self.video_file_edit.text() != "":
            self.thread.start_with_params(self.video_file_edit.text(),
                                          int(self.time_step_combo.currentText()),
                                          self.landing_time_edit.text(),
                                          self.death_time_edit.text(),
                                          self.output_file_edit.text(),
                                          self.path_color)


if __name__ == "__main__":
    app = PUBGISApplication(sys.argv)
    win = PUBGISMainWindow()

    sys.exit(app.exec_())
