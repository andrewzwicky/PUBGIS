import os

import cv2
from PyQt5 import QtCore, uic
from PyQt5.QtCore import QThread, QTime
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QGraphicsScene, QColorDialog

from pubgis.color import Color, Space, Scaling
from pubgis.match import PUBGISMatch, DEFAULT_PATH_COLOR
from pubgis.video_iterator import VideoIterator


class PUBGISWorkerThread(QThread):
    percent_update = QtCore.pyqtSignal(int)
    percent_max_update = QtCore.pyqtSignal(int)
    minimap_update = QtCore.pyqtSignal(QImage)

    def __init__(self, parent, minimap_iterator, output_file, path_color):
        super(PUBGISWorkerThread, self).__init__(parent)
        self.minimap_iterator = minimap_iterator
        self.output_file = output_file
        self.path_color = path_color

    def run(self):
        self.percent_max_update.emit(0)

        match = PUBGISMatch(minimap_iterator=self.minimap_iterator,
                            output_file=self.output_file,
                            path_color=self.path_color)

        img2 = cv2.cvtColor(PUBGISMatch.map, cv2.COLOR_BGR2RGB)
        height, width, _ = img2.shape
        bytes_per_line = 3 * width
        qimg = QImage(img2.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.minimap_update.emit(qimg)

        percent_init = False

        for percent, progress_minimap in match.process_match():
            if self.isInterruptionRequested():
                break

            if not percent_init:
                self.percent_max_update.emit(100)
                percent_init = True
            self.percent_update.emit(percent)
            img2 = cv2.cvtColor(progress_minimap, cv2.COLOR_BGR2RGB)
            height, width, _ = img2.shape
            bytes_per_line = 3 * width
            qimg = QImage(img2.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.minimap_update.emit(qimg)

        if self.isInterruptionRequested():
            self.percent_update.emit(0)
            self.percent_max_update.emit(100)
        else:
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

        self.map_creation_view.setScene(QGraphicsScene())
        self.map_pixmap = self.map_creation_view.scene().addPixmap(QPixmap())

        self.path_color = DEFAULT_PATH_COLOR
        self.update_path_color_preview()

        self.video_file_edit.setText(r"E:\Movies\OBS\2017-09-07_20-16-43.mp4")
        self.landing_time.setDisplayFormat("m:ss")
        self.death_time.setDisplayFormat("m:ss")

        self.show()

        self.buttons = [self.video_file_browse_button,
                        self.output_file_browse_button,
                        self.color_select_button,
                        self.process_button,
                        self.time_step_combo,
                        self.landing_time,
                        self.death_time,
                        self.output_file_edit,
                        self.video_file_edit]

    def _select_video_file(self):
        fname, _ = QFileDialog.getOpenFileName(directory=os.path.expanduser('~'),
                                               filter="Videos (*.mp4)")
        self.video_file_edit.setText(fname)

        self.output_file_edit.setText(os.path.join(os.path.dirname(fname), os.path.splitext(fname)[0] + '.jpg'))

    def _select_output_file(self):
        fname, _ = QFileDialog.getSaveFileName(directory=os.path.expanduser('~'),
                                               filter="Images (*.jpg)")
        self.output_file_edit.setText(fname)

    def select_background_color(self):
        color_dialog = QColorDialog(QColor(*self.path_color(alpha=True)))
        *picker_rgb, alpha = color_dialog.getColor(options=QColorDialog.ShowAlphaChannel).getRgb()
        self.path_color = Color(picker_rgb, scaling=Scaling.UINT8, alpha=alpha)
        self.update_path_color_preview()

    def update_path_color_preview(self):
        style = "background-color:rgb({},{},{})".format(*self.path_color(space=Space.RGB))
        self.path_color_preview.setStyleSheet(style)

    def update_map_preview(self, qimg):
        self.map_pixmap.setPixmap(QPixmap.fromImage(qimg))
        self.map_creation_view.fitInView(self.map_creation_view.scene().itemsBoundingRect())
        self.map_creation_view.update()
        self.map_creation_view.repaint()

    def disable_buttons(self):
        for control in self.buttons:
            control.setEnabled(False)

    def enable_buttons(self):
        for control in self.buttons:
            control.setEnabled(True)

    def process_match(self):
        if self.video_file_edit.text() != "":
            self.disable_buttons()

            video_iter = VideoIterator(video_file=self.video_file_edit.text(),
                                       landing_time=QTime(0, 0, 0).secsTo(self.landing_time.time()),
                                       death_time=QTime(0, 0, 0).secsTo(self.death_time.time()),
                                       step_interval=int(self.time_step_combo.currentText()))

            match_thread = PUBGISWorkerThread(self,
                                              minimap_iterator=video_iter,
                                              output_file=self.output_file_edit.text(),
                                              path_color=self.path_color)
            match_thread.percent_update.connect(self.progress_bar.setValue)
            match_thread.percent_max_update.connect(self.progress_bar.setMaximum)
            match_thread.minimap_update.connect(self.update_map_preview)
            match_thread.finished.connect(self.enable_buttons)
            self.cancel_button.released.connect(match_thread.requestInterruption)
            match_thread.start()
