import os
from datetime import datetime
from enum import IntEnum, Flag, auto

import cv2
import mss
import numpy as np
from PyQt5 import QtCore, uic
from PyQt5.QtCore import QThread, QTime, Qt, QRectF, QDir
from PyQt5.QtGui import QPixmap, QImage, QColor, QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QGraphicsScene, QColorDialog, QMessageBox

from pubgis.color import Color, Scaling
from pubgis.match import PUBGISMatch, DEFAULT_PATH_COLOR
from pubgis.minimap_iterators.generic import ResolutionNotSupportedException
from pubgis.minimap_iterators.live import LiveFeed
from pubgis.minimap_iterators.video import VideoIterator

PATH_PREVIEW_POINTS = [(0, 0), (206, 100), (50, 50), (10, 180)]


class ProcessMode(IntEnum):
    VIDEO = 0
    LIVE = 1


class ButtonGroups(Flag):
    PREPROCESS = auto()
    PROCESSING = auto()


class PUBGISWorkerThread(QThread):
    percent_update = QtCore.pyqtSignal(int)
    percent_max_update = QtCore.pyqtSignal(int)
    minimap_update = QtCore.pyqtSignal(np.ndarray)

    def __init__(self,  # pylint: disable=too-many-arguments
                 parent, minimap_iterator, output_file, path_color, path_thickness):
        super(PUBGISWorkerThread, self).__init__(parent)
        self.minimap_iterator = minimap_iterator
        self.output_file = output_file
        self.path_color = path_color
        self.path_thickness = path_thickness

    def run(self):
        self.percent_max_update.emit(0)
        self.percent_update.emit(0)

        match = PUBGISMatch(minimap_iterator=self.minimap_iterator,
                            path_color=self.path_color,
                            path_thickness=self.path_thickness)

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
        match.create_output(self.output_file)


class PUBGISMainWindow(QMainWindow):  # pylint: disable=too-many-instance-attributes
    changed_percent = QtCore.pyqtSignal(int)
    update_minimap = QtCore.pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "pubgis_gui.ui"), self)

        # connect buttons to functions
        self.color_select_button.released.connect(self._select_background_color)
        self.process_button.released.connect(self.process_match)
        self.video_file_browse_button.clicked.connect(self._select_video_file)
        self.output_file_browse_button.clicked.connect(self._select_output_file)
        self.output_directory_browse_button.clicked.connect(self._select_output_directory)
        self.tabWidget.currentChanged.connect(self._parse_available_monitors)
        self.monitor_combo.currentIndexChanged.connect(self._update_monitor_preview)
        self.thickness_spinbox.valueChanged.connect(self._update_path_color_preview)

        # prepare path preview
        self.path_color = DEFAULT_PATH_COLOR
        self.path_preview_image = cv2.imread(os.path.join(os.path.dirname(__file__),
                                                          "images",
                                                          "path_preview_minimap.jpg"))
        self.path_preview_view.setScene(QGraphicsScene())
        self.path_pixmap = self.path_preview_view.scene().addPixmap(QPixmap())

        # prepare map preview
        self.map_creation_view.setScene(QGraphicsScene())
        self.map_pixmap = self.map_creation_view.scene().addPixmap(QPixmap())

        # set window name and icon
        self.setWindowTitle("PUBGIS")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__),
                                              "images",
                                              "icons",
                                              "navigation.png")))

        # initialize default directories
        self.last_video_file_dir = PUBGISMainWindow._get_starting_directory()
        self.last_output_file_dir = PUBGISMainWindow._get_starting_directory()
        self.last_output_live_dir = PUBGISMainWindow._get_starting_directory()

        self._set_output_directory(self.last_output_file_dir)

        # This is the list of buttons and when they should be active.
        self.buttons = {ButtonGroups.PREPROCESS:
                            [self.video_file_browse_button,
                             self.output_file_browse_button,
                             self.output_directory_browse_button,
                             self.color_select_button,
                             self.process_button,
                             self.time_step,
                             self.landing_time,
                             self.death_time,
                             self.output_file_edit,
                             self.output_directory_edit,
                             self.video_file_edit,
                             self.tabWidget,
                             self.thickness_spinbox],
                        ButtonGroups.PROCESSING: [self.cancel_button]}

        self._update_button_state(ButtonGroups.PREPROCESS)

        self.show()
        self._update_path_color_preview()

    @staticmethod
    def _get_starting_directory():
        user_dir = os.path.expanduser('~')
        desktop = os.path.join(user_dir, "Desktop")
        if os.path.exists(desktop):
            return desktop

        return user_dir

    @staticmethod
    def _update_view_with_image(view, pixmap, image_array):
        image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        height, width, _ = image.shape
        bytes_per_line = 3 * width
        qimg = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)

        # noinspection PyCallByClass
        pixmap.setPixmap(QPixmap.fromImage(qimg))
        PUBGISMainWindow._fit_in_view(view,
                                      view.scene().itemsBoundingRect(),
                                      flags=Qt.KeepAspectRatio)

    @staticmethod
    def generate_output_file_name():
        return "pubgis_{}.jpg".format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

    # pylint: disable=line-too-long
    # https://github.com/nevion/pyqimageview/blob/0f0e2966d2a2a089ec80b5bf777a773443df7f9e/qimageview/widget.py#L275-L291
    # pylint: enable=line-too-long
    # Copyright (c) 2014 Jason Newton <nevion@gmail.com>
    # MIT License
    # override arbitrary and unwanted margins: https://bugreports.qt.io/browse/QTBUG-42331
    @staticmethod
    def _fit_in_view(view, rect, flags=Qt.IgnoreAspectRatio):
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

    # VIDEO SECTION

    def _set_video_file(self, fname):
        """
        Given a video file name, set the video_file_edit text to this file name and
        auto-fill the output file name as well.
        """
        if fname:
            self.last_video_file_dir = os.path.dirname(fname)
            self.video_file_edit.setText(QDir.toNativeSeparators(fname))

            video_filename, _ = os.path.splitext(os.path.basename(fname))

            self._set_output_file(os.path.join(self.last_output_file_dir,
                                               f"{video_filename}.jpg"))

    def _select_video_file(self):
        fname, _ = QFileDialog.getOpenFileName(directory=self.last_video_file_dir,
                                               filter="Videos (*.mp4)")
        self._set_video_file(fname)

    def _set_output_file(self, fname):
        if fname:
            self.last_output_file_dir = os.path.dirname(fname)
            self.output_file_edit.setText(QDir.toNativeSeparators(fname))

    def _select_output_file(self):
        fname, _ = QFileDialog.getSaveFileName(directory=self.last_output_file_dir,
                                               filter="Images (*.jpg)")
        self._set_output_file(fname)

    # LIVE SECTION

    def _set_output_directory(self, dname):
        if dname:
            self.last_output_live_dir = dname
            self.output_directory_edit.setText(QDir.toNativeSeparators(dname))

    def _select_output_directory(self):
        dname = QFileDialog.getExistingDirectory(directory=self.last_output_live_dir,
                                                 options=QFileDialog.ShowDirsOnly)
        self._set_output_directory(dname)

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
        with mss.mss() as sct:
            cap = np.array(sct.grab(sct.monitors[self.monitor_combo.currentIndex() + 1]))[:, :, :3]
        self._update_view_with_image(self.map_creation_view, self.map_pixmap, cap)

    # UNIVERSAL, APPLIES TO ALL SECTIONS

    def _select_background_color(self):
        color_dialog = QColorDialog(QColor(*self.path_color(alpha=True)))
        *picker_rgb, alpha = color_dialog.getColor(options=QColorDialog.ShowAlphaChannel).getRgb()
        self.path_color = Color(picker_rgb, scaling=Scaling.UINT8, alpha=alpha)
        self._update_path_color_preview()

    def _update_path_color_preview(self):
        path_image = np.copy(self.path_preview_image)
        for start, end in zip(PATH_PREVIEW_POINTS[:-1], PATH_PREVIEW_POINTS[1:]):
            cv2.line(path_image,
                     start,
                     end,
                     color=self.path_color(),
                     thickness=self.thickness_spinbox.value(),
                     lineType=cv2.LINE_AA)
        self._update_view_with_image(self.path_preview_view, self.path_pixmap, path_image)

    def _update_map_preview(self, minimap):
        self._update_view_with_image(self.map_creation_view, self.map_pixmap, minimap)

    # This has a default argument so that it can be slotted to a signal
    # like the .finished signal and that will reset the buttons.
    def _update_button_state(self, active_groups=ButtonGroups.PREPROCESS):
        for group, controls in self.buttons.items():
            for control in controls:
                control.setEnabled(bool(group & active_groups))

    def _validate_inputs(self, mode):
        if mode == ProcessMode.VIDEO:
            # video file exists
            # output folder exists, writable
            if not os.path.exists(self.video_file_edit.text()):
                QMessageBox.information(self, "Error", "video file not found")
                return False

            if not os.path.exists(os.path.dirname(self.output_file_edit.text())):
                QMessageBox.information(self, "Error", "output directory not writeable")
                return False

        if mode == ProcessMode.LIVE:
            if not os.path.exists(self.output_directory_edit.text()):
                QMessageBox.information(self, "Error", "output directory not writeable")
                return False

        return True

    def process_match(self):
        map_iter = None
        output_file = None

        try:
            if self.tabWidget.currentIndex() == ProcessMode.VIDEO:
                if self._validate_inputs(ProcessMode.VIDEO):
                    zero = QTime(0, 0, 0)
                    map_iter = VideoIterator(video_file=self.video_file_edit.text(),
                                             landing_time=zero.secsTo(self.landing_time.time()),
                                             death_time=zero.secsTo(self.death_time.time()),
                                             step_interval=float(self.time_step.currentText()))
                    output_file = self.output_file_edit.text()

            elif self.tabWidget.currentIndex() == ProcessMode.LIVE:
                if self._validate_inputs(ProcessMode.LIVE):
                    map_iter = LiveFeed(time_step=float(self.time_step.currentText()),
                                        monitor=self.monitor_combo.currentIndex() + 1)

                    output_file = os.path.join(self.output_directory_edit.text(),
                                               self.generate_output_file_name())
            else:
                raise ValueError

            if map_iter:
                match_thread = PUBGISWorkerThread(self,
                                                  minimap_iterator=map_iter,
                                                  output_file=output_file,
                                                  path_color=self.path_color,
                                                  path_thickness=self.thickness_spinbox.value())

                self._update_button_state(ButtonGroups.PROCESSING)
                match_thread.percent_update.connect(self.progress_bar.setValue)
                match_thread.percent_max_update.connect(self.progress_bar.setMaximum)
                match_thread.minimap_update.connect(self._update_map_preview)
                match_thread.finished.connect(self._update_button_state)
                self.cancel_button.released.connect(match_thread.requestInterruption)
                match_thread.start()

        except ResolutionNotSupportedException:
            QMessageBox.information(self, "Error", "Resolution not supported")
