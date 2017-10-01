import os
from threading import RLock

import cv2
import mss
import numpy as np
from PyQt5 import QtCore, uic
from PyQt5.QtCore import QThread, QTime, Qt, QRectF
from PyQt5.QtGui import QPixmap, QImage, QColor, QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QGraphicsScene, QColorDialog, QMessageBox

from pubgis.color import Color, Space, Scaling
from pubgis.match import PUBGISMatch, DEFAULT_PATH_COLOR
from pubgis.minimap_iterators.generic import ResolutionNotSupportedException
from pubgis.minimap_iterators.live import LiveFeed
from pubgis.minimap_iterators.video import VideoIterator


class PUBGISWorkerThread(QThread):
    percent_update = QtCore.pyqtSignal(int)
    percent_max_update = QtCore.pyqtSignal(int)
    minimap_update = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent, minimap_iterator, output_file, path_color):
        super(PUBGISWorkerThread, self).__init__(parent)
        self.minimap_iterator = minimap_iterator
        self.output_file = output_file
        self.path_color = path_color

    def run(self):
        self.percent_max_update.emit(0)
        self.percent_update.emit(0)

        match = PUBGISMatch(minimap_iterator=self.minimap_iterator,
                            output_file=self.output_file,
                            path_color=self.path_color)

        self.minimap_update.emit(match.map)

        for percent, progress_minimap in match.process_match():
            if percent is not None:
                self.percent_max_update.emit(100)
                self.percent_update.emit(percent)
            self.minimap_update.emit(progress_minimap)

            if self.isInterruptionRequested():
                self.minimap_iterator.stop()

        if self.isInterruptionRequested():
            self.percent_max_update.emit(100)

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
        self.tabWidget.currentChanged.connect(self._parse_available_monitors)
        self.monitor_combo.currentIndexChanged.connect(self._update_monitor_preview)

        self.map_creation_view.setScene(QGraphicsScene())
        self.map_pixmap = self.map_creation_view.scene().addPixmap(QPixmap())

        self.path_color = DEFAULT_PATH_COLOR
        self.update_path_color_preview()

        self.last_video_file_directory = os.path.expanduser('~')
        self.last_output_file_directory = os.path.expanduser('~')

        self.setWindowTitle("PUBGIS")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__),
                                              "images",
                                              "icons",
                                              "navigation.png")))

        self.preview_lock = RLock()
        self.progress_bar_lock = RLock()
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)

        self.setAcceptDrops(True)

        self.buttons = {'preprocess': [self.video_file_browse_button,
                                       self.output_file_browse_button,
                                       self.color_select_button,
                                       self.process_button,
                                       self.time_step,
                                       self.landing_time,
                                       self.death_time,
                                       self.output_file_edit,
                                       self.video_file_edit,
                                       self.tabWidget],
                        'during': [self.cancel_button]}

        self.enable_selection_buttons()

        self.show()

    # pylint: disable=line-too-long
    # https://github.com/nevion/pyqimageview/blob/0f0e2966d2a2a089ec80b5bf777a773443df7f9e/qimageview/widget.py#L275-L291
    # pylint: enable=line-too-long
    # Copyright (c) 2014 Jason Newton <nevion@gmail.com>
    # MIT License
    # override arbitrary and unwanted margins: https://bugreports.qt.io/browse/QTBUG-42331
    @staticmethod
    def fit_in_view(view, rect, flags=Qt.IgnoreAspectRatio):
        if view.scene() is None or rect.isNull():
            return
        view.last_scene_roi = rect
        unity = view.transform().mapRect(QRectF(0, 0, 1, 1))
        view.scale(1 / unity.width(), 1 / unity.height())
        view_rect = view.viewport().rect()
        scene_rect = view.transform().mapRect(rect)
        xratio = view_rect.width() / scene_rect.width()
        yratio = view_rect.height() / scene_rect.height()
        if flags == Qt.KeepAspectRatio:
            xratio = yratio = min(xratio, yratio)
        elif flags == Qt.KeepAspectRatioByExpanding:
            xratio = yratio = max(xratio, yratio)
        view.scale(xratio, yratio)
        view.centerOn(rect.center())

    # name must match because we're overriding QMainWindow method
    def dragEnterEvent(self, event):  # pylint: disable=invalid-name, no-self-use
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    # name must match because we're overriding QMainWindow method
    def dropEvent(self, event):  # pylint: disable=invalid-name
        if event.mimeData().hasUrls:
            fname = event.mimeData().urls()[0].toLocalFile()
            self._set_video_file(fname)

    def _set_video_file(self, fname):
        self.last_video_file_directory = os.path.dirname(fname)
        self.video_file_edit.setText(fname)

        if os.path.exists(fname):
            self.output_file_edit.setText(os.path.join(os.path.dirname(fname),
                                                       os.path.splitext(fname)[0] + '.jpg'))

    def _select_video_file(self):
        fname, _ = QFileDialog.getOpenFileName(directory=self.last_video_file_directory,
                                               filter="Videos (*.mp4)")
        self._set_video_file(fname)

    def _select_output_file(self):
        fname, _ = QFileDialog.getSaveFileName(directory=self.last_output_file_directory,
                                               filter="Images (*.jpg)")
        self.last_output_file_directory = os.path.dirname(fname)
        self.output_file_edit.setText(fname)

    def _parse_available_monitors(self, mon_combo_index):
        if mon_combo_index == 1 and self.monitor_combo.count() == 0:
            self.monitor_combo.clear()

            sizes = []

            with mss.mss() as sct:
                for index, monitor in enumerate(sct.monitors[1:], start=1):
                    sizes.append(f"{index}: {monitor['width']}x{monitor['height']}")

            self.monitor_combo.insertItems(0, sizes)
            self._update_monitor_preview()

    def _update_monitor_preview(self):
        self.preview_lock.acquire()
        with mss.mss() as sct:
            cap = np.array(sct.grab(sct.monitors[self.monitor_combo.currentIndex() + 1]))[:, :, :3]

        img2 = cv2.cvtColor(cap, cv2.COLOR_BGR2RGB)
        height, width, _ = img2.shape
        bytes_per_line = 3 * width
        qimg = QImage(img2.data, width, height, bytes_per_line, QImage.Format_RGB888)
        # noinspection PyCallByClass
        self.map_pixmap.setPixmap(QPixmap.fromImage(qimg))
        self.fit_in_view(self.map_creation_view,
                         self.map_creation_view.scene().itemsBoundingRect(),
                         flags=Qt.KeepAspectRatio)
        self.preview_lock.release()

    def select_background_color(self):
        color_dialog = QColorDialog(QColor(*self.path_color(alpha=True)))
        *picker_rgb, alpha = color_dialog.getColor(options=QColorDialog.ShowAlphaChannel).getRgb()
        self.path_color = Color(picker_rgb, scaling=Scaling.UINT8, alpha=alpha)
        self.update_path_color_preview()

    def update_path_color_preview(self):
        style = "background-color:rgb({},{},{})".format(*self.path_color(space=Space.RGB))
        self.path_color_preview.setStyleSheet(style)

    def update_map_preview(self, minimap):
        self.preview_lock.acquire()
        img2 = cv2.cvtColor(minimap, cv2.COLOR_BGR2RGB)
        height, width, _ = img2.shape
        bytes_per_line = 3 * width
        qimg = QImage(img2.data, width, height, bytes_per_line, QImage.Format_RGB888)
        # noinspection PyCallByClass
        self.map_pixmap.setPixmap(QPixmap.fromImage(qimg))
        self.fit_in_view(self.map_creation_view, self.map_creation_view.scene().itemsBoundingRect())
        self.preview_lock.release()

    def update_pbar_max(self, maximum):
        self.progress_bar_lock.acquire()
        self.progress_bar.setMaximum(maximum)
        self.progress_bar_lock.release()

    def update_pbar_value(self, progress):
        self.progress_bar_lock.acquire()
        self.progress_bar.setValue(progress)
        self.progress_bar_lock.release()

    def disable_selection_buttons(self):
        for control in self.buttons['preprocess']:
            control.setEnabled(False)
        for control in self.buttons['during']:
            control.setEnabled(True)

    def enable_selection_buttons(self):
        for control in self.buttons['preprocess']:
            control.setEnabled(True)
        for control in self.buttons['during']:
            control.setEnabled(False)

    def process_match(self):
        map_iter = None

        try:
            if self.tabWidget.currentIndex() == 0:
                if self.video_file_edit.text() != "":
                    zero = QTime(0, 0, 0)
                    map_iter = VideoIterator(video_file=self.video_file_edit.text(),
                                             landing_time=zero.secsTo(self.landing_time.time()),
                                             death_time=zero.secsTo(self.death_time.time()),
                                             step_interval=float(self.time_step.currentText()))

            if self.tabWidget.currentIndex() == 1:
                map_iter = LiveFeed(time_step=float(self.time_step.currentText()),
                                    monitor=self.monitor_combo.currentIndex() + 1)
        except ResolutionNotSupportedException:
            res_message = QMessageBox()
            res_message.setText("This resolution is not supported")
            res_message.exec()

        if map_iter:
            self.disable_selection_buttons()

            match_thread = PUBGISWorkerThread(self,
                                              minimap_iterator=map_iter,
                                              output_file=self.output_file_edit.text(),
                                              path_color=self.path_color)
            match_thread.percent_update.connect(self.update_pbar_value)
            match_thread.percent_max_update.connect(self.update_pbar_max)
            match_thread.minimap_update.connect(self.update_map_preview)
            match_thread.finished.connect(self.enable_selection_buttons)
            self.cancel_button.released.connect(match_thread.requestInterruption)
            match_thread.start()
