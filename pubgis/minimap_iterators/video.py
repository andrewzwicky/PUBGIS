import os

import cv2

from pubgis.minimap_iterators.generic import GenericIterator

DEFAULT_STEP = 1


class VideoIterator(GenericIterator):  # pylint: disable=too-many-instance-attributes
    def __init__(self, video_file=None, landing_time=0, time_step=DEFAULT_STEP, death_time=None):
        super().__init__()
        if not os.path.isfile(video_file):
            raise FileNotFoundError(video_file)

        if landing_time < 0:
            raise ValueError("landing time must be >= 0")

        if death_time is not None and death_time < landing_time:
            raise ValueError("death time must be greater than landing time")

        self.cap = cv2.VideoCapture(video_file)
        self.frame_index = self.get_minimap_slice(int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                                  int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.landing_frame = int(landing_time * self.fps)
        self.time_step = time_step
        self.step_frames = max(int(time_step * self.fps), 1) - 1
        if death_time:
            death_frame = int(death_time * self.fps)
        else:
            death_frame = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frames_processed = 0
        self.frames_to_process = death_frame - self.landing_frame

    def __iter__(self):
        for _ in range(self.landing_frame):
            self.cap.grab()
        return self

    def __next__(self):
        self.check_for_stop()

        grabbed, frame = self.cap.read()
        timestamp = self.frames_processed / self.fps
        self.frames_processed += 1

        if grabbed and self.frames_processed < self.frames_to_process:
            minimap = frame[self.frame_index]
            percent = min((self.frames_processed / self.frames_to_process) * 100, 100)

            for _ in range(self.step_frames):
                self.cap.grab()
            self.frames_processed += self.step_frames

            return percent, timestamp, minimap
        else:
            raise StopIteration
