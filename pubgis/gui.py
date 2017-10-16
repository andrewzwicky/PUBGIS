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

from pubgis import __version__
from pubgis.color import Color, Scaling
from pubgis.match import PUBGISMatch
from pubgis.minimap_iterators.generic import ResolutionNotSupportedException
from pubgis.minimap_iterators.live import LiveFeed
from pubgis.minimap_iterators.video import VideoIterator
from pubgis.output.json import output_json, create_json_data
from pubgis.output.output_enum import OutputFlags
from pubgis.output.plotting import PATH_COLOR, PATH_THICKNESS
from pubgis.output.plotting import plot_coordinate_line, create_output_opencv
from pubgis.support import find_path_bounds, create_slice

PATH_PREVIEW_POINTS = [(0, 0), (206, 100), (50, 50), (10, 180)]


class ProcessMode(IntEnum):
    VIDEO = 0
    LIVE = 1


class ButtonGroups(Flag):
    PREPROCESS = auto()
    PROCESSING = auto()


class PUBGISWorkerThread(QThread): # pylint: disable=too-many-instance-attributes
    percent_update = QtCore.pyqtSignal(int)
    percent_max_update = QtCore.pyqtSignal(int)
    minimap_update = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent, minimap_iterator, output_file, output_flags):
        super(PUBGISWorkerThread, self).__init__(parent)
        self.parent = parent
        self.minimap_iterator = minimap_iterator
        self.output_file = output_file
        self.full_positions = []
        self.timestamps = []
        self.base_map_alpha = cv2.cvtColor(PUBGISMatch.full_map, cv2.COLOR_BGR2BGRA)
        self.preview_map = cv2.cvtColor(PUBGISMatch.full_map, cv2.COLOR_BGR2BGRA)
        self.output_flags = output_flags

    def run(self):
        self.percent_max_update.emit(0)
        self.percent_update.emit(0)

        match = PUBGISMatch(self.minimap_iterator, debug=False)

        self.minimap_update.emit(self.preview_map)

        for percent, timestamp, full_position in match.process_match():
            if percent is not None:
                self.percent_max_update.emit(100)
                self.percent_update.emit(percent)

            plot_coordinate_line(self.preview_map,
                                 self.full_positions,
                                 full_position,
                                 self.parent.path_color(),
                                 self.parent.thickness_spinbox.value())

            self.full_positions.append(full_position)
            self.timestamps.append(timestamp)

            if self.output_flags & OutputFlags.LIVE_PREVIEW:
                preview_coords, preview_size = find_path_bounds(PUBGISMatch.full_map.shape[0],
                                                                self.full_positions)

                preview_slice = create_slice(preview_coords, preview_size)

                alpha = self.parent.path_color.alpha
                blended = cv2.addWeighted(self.base_map_alpha[preview_slice],
                                          1 - alpha,
                                          self.preview_map[preview_slice],
                                          alpha,
                                          0)

                self.minimap_update.emit(blended)

            if self.isInterruptionRequested():
                self.minimap_iterator.stop()

        if self.isInterruptionRequested():
            self.percent_max_update.emit(100)

        self.percent_update.emit(100)

        alpha = self.parent.path_color.alpha

        if self.output_flags & OutputFlags.FULL_MAP:
            blended = cv2.addWeighted(self.base_map_alpha, 1 - alpha, self.preview_map, alpha, 0)
            create_output_opencv(blended,
                                 self.full_positions,
                                 self.output_file,
                                 full_map=True)
        elif self.output_flags & OutputFlags.CROPPED_MAP:
            blended = cv2.addWeighted(self.base_map_alpha, 1 - alpha, self.preview_map, alpha, 0)
            create_output_opencv(blended,
                                 self.full_positions,
                                 self.output_file)

        if self.output_flags & OutputFlags.JSON:
            pre, _ = os.path.splitext(self.output_file)
            json_file = pre + ".json"
            data = create_json_data(self.full_positions, self.timestamps)
            output_json(json_file, data)


class PUBGISMainWindow(QMainWindow):
    changed_percent = QtCore.pyqtSignal(int)
    update_minimap = QtCore.pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "pubgis_gui.ui"), self)

        # connect buttons to functions
        self.color_select_button.released.connect(self._select_path_color)
        self.process_button.released.connect(self.process_match)
        self.video_file_browse_button.clicked.connect(self._select_video_file)
        self.output_file_browse_button.clicked.connect(self._select_output_file)
        self.output_directory_browse_button.clicked.connect(self._select_output_directory)
        self.tabWidget.currentChanged.connect(self._parse_available_monitors)
        self.monitor_combo.currentIndexChanged.connect(self._update_monitor_preview)
        self.thickness_spinbox.valueChanged.connect(self._update_path_color_preview)

        # prepare path preview
        self.path_color = PATH_COLOR

        self.path_preview_view.setScene(QGraphicsScene())
        self.path_preview_view.scene().addPixmap(QPixmap())

        # prepare map preview
        self.map_creation_view.setScene(QGraphicsScene())
        self.map_creation_view.scene().addPixmap(QPixmap())

        # set window name and icon
        self.setWindowTitle("PUBGIS (v{})".format(__version__))
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
        configuration_buttons = [self.video_file_browse_button,
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
                                 self.thickness_spinbox,
                                 self.disable_preview_checkbox,
                                 self.output_full_map_checkbox,
                                 self.output_json_checkbox]

        self.buttons = {ButtonGroups.PREPROCESS: configuration_buttons,
                        ButtonGroups.PROCESSING: [self.cancel_button]}

        self._update_button_state(ButtonGroups.PREPROCESS)

        self.show()
        self.thickness_spinbox.setValue(PATH_THICKNESS)
        self._update_path_color_preview()

    @staticmethod
    def _get_starting_directory():
        user_dir = os.path.expanduser('~')
        desktop = os.path.join(user_dir, "Desktop")
        if os.path.exists(desktop):
            return desktop

        return user_dir

    @staticmethod
    def _update_view_with_image(view, image_array):
        image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        height, width, _ = image.shape
        bytes_per_line = 3 * width
        qimg = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)

        # noinspection PyCallByClass
        view.scene().items()[0].setPixmap(QPixmap.fromImage(qimg))
        PUBGISMainWindow._fit_in_view(view,
                                      view.scene().itemsBoundingRect(),
                                      flags=Qt.KeepAspectRatio)

    @staticmethod
    def generate_output_file_name():
        return "pubgis_{}.jpg".format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

    # https://github.com/nevion/pyqimageview/blob/master/qimageview/widget.py#L275-L291
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
            file_name = event.mimeData().urls()[0].toLocalFile()
            self._set_video_file(file_name)

    # VIDEO SECTION

    def _set_video_file(self, file_name):
        """
        Given a video file name, set the video_file_edit text to this file name and
        auto-fill the output file name as well.
        """
        if file_name:
            self.last_video_file_dir = os.path.dirname(file_name)
            self.video_file_edit.setText(QDir.toNativeSeparators(file_name))

            video_filename, _ = os.path.splitext(os.path.basename(file_name))

            self._set_output_file(os.path.join(self.last_output_file_dir,
                                               f"{video_filename}.jpg"))

    def _select_video_file(self):
        file_name, _ = QFileDialog.getOpenFileName(directory=self.last_video_file_dir,
                                                   filter="Videos (*.mp4)")
        self._set_video_file(file_name)

    def _set_output_file(self, file_name):
        if file_name:
            self.last_output_file_dir = os.path.dirname(file_name)
            self.output_file_edit.setText(QDir.toNativeSeparators(file_name))

    def _select_output_file(self):
        file_name, _ = QFileDialog.getSaveFileName(directory=self.last_output_file_dir,
                                                   filter="Images (*.jpg)")
        self._set_output_file(file_name)

    # LIVE SECTION

    def _set_output_directory(self, dir_name):
        if dir_name:
            self.last_output_live_dir = dir_name
            self.output_directory_edit.setText(QDir.toNativeSeparators(dir_name))

    def _select_output_directory(self):
        dir_name = QFileDialog.getExistingDirectory(directory=self.last_output_live_dir,
                                                    options=QFileDialog.ShowDirsOnly)
        self._set_output_directory(dir_name)

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
            # Monitor 0 is all of the monitors glued together.  This was skipped when the monitors
            # were added to the monitor_combo, so we must add 1 to the index when previewing
            # to make sure the right monitor is displayed.
            cap = np.array(sct.grab(sct.monitors[self.monitor_combo.currentIndex() + 1]))[:, :, :3]
        self._update_view_with_image(self.map_creation_view, cap)

    # UNIVERSAL, APPLIES TO ALL SECTIONS

    def _select_path_color(self):
        color_dialog = QColorDialog(QColor(*self.path_color(alpha=True)))
        *picker_rgb, alpha = color_dialog.getColor(options=QColorDialog.ShowAlphaChannel).getRgb()
        self.path_color = Color(picker_rgb, scaling=Scaling.UINT8, alpha=alpha)
        self._update_path_color_preview()

    def _update_path_color_preview(self):
        path_image_base = np.copy(PUBGISMatch.full_map[create_slice((2943, 2913), 240)])
        path_image = np.copy(PUBGISMatch.full_map[create_slice((2943, 2913), 240)])

        for start, end in zip(PATH_PREVIEW_POINTS[:-1], PATH_PREVIEW_POINTS[1:]):
            plot_coordinate_line(path_image,
                                 [start],
                                 end,
                                 self.path_color(),
                                 self.thickness_spinbox.value())

        alpha = self.path_color.alpha
        blended = cv2.addWeighted(path_image_base, 1 - alpha, path_image, alpha, 0)

        self._update_view_with_image(self.path_preview_view, blended)

    def _update_map_preview(self, minimap):
        self._update_view_with_image(self.map_creation_view, minimap)

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
                QMessageBox.information(self, "Error", "output directory doesn't exist")
                return False

        if mode == ProcessMode.LIVE:
            if not os.path.exists(self.output_directory_edit.text()):
                QMessageBox.information(self, "Error", "output directory doesn't exist")
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
                                             time_step=float(self.time_step.currentText()))
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
                output_flags = OutputFlags.NO_OUTPUT
                output_flags |= OutputFlags.LIVE_PREVIEW
                output_flags |= OutputFlags.CROPPED_MAP

                if self.disable_preview_checkbox.isChecked():
                    output_flags ^= OutputFlags.LIVE_PREVIEW

                if self.output_json_checkbox.isChecked():
                    output_flags |= OutputFlags.JSON

                if self.output_full_map_checkbox.isChecked():
                    output_flags |= OutputFlags.FULL_MAP

                match_thread = PUBGISWorkerThread(self,
                                                  map_iter,
                                                  output_file,
                                                  output_flags)

                self._update_button_state(ButtonGroups.PROCESSING)
                match_thread.percent_update.connect(self.progress_bar.setValue)
                match_thread.percent_max_update.connect(self.progress_bar.setMaximum)
                match_thread.minimap_update.connect(self._update_map_preview)
                match_thread.finished.connect(self._update_button_state)
                self.cancel_button.released.connect(match_thread.requestInterruption)
                match_thread.start()

        except ResolutionNotSupportedException:
            QMessageBox.information(self, "Error", "Resolution not supported")
