from threading import RLock

import cv2

from pubgis.match import MMAP_HEIGHT, MMAP_WIDTH, MMAP_X, MMAP_Y

DEFAULT_STEP_INTERVAL = 1


class VideoIterator:
    def __init__(self,
                 video_file=None,
                 landing_time=0,
                 step_interval=DEFAULT_STEP_INTERVAL,
                 death_time=None,):
        self.cap = cv2.VideoCapture(video_file)
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.landing_frame = int(landing_time * fps)
        self.step_frames = max(int(step_interval * fps), 1) - 1
        # TODO: assert death time > landing_time
        if death_time:
            death_frame = int(death_time * fps)
        else:
            death_frame = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frames_processed = 0
        self.frames_to_process = death_frame - self.landing_frame
        self.stop_requested = False
        self._lock = RLock()

    def __iter__(self):
        for _ in range(self.landing_frame):
            self.cap.grab()
        return self

    def __next__(self):
        self._lock.acquire()
        grabbed, frame = self.cap.read()
        self.frames_processed += 1

        if grabbed and not self.stop_requested:
            if frame.shape == (1080, 1920, 3):
                minimap = frame[MMAP_Y:MMAP_Y + MMAP_HEIGHT, MMAP_X:MMAP_X + MMAP_WIDTH]
            else:
                raise ValueError("Only 1920x1800 video is supported at this time.")

            percent = min(int((self.frames_processed / self.frames_to_process) * 100), 100)

            for _ in range(self.step_frames):
                self.cap.grab()
            self.frames_processed += self.step_frames

            self._lock.release()
            return percent, minimap
        else:
            self._lock.release()
            raise StopIteration

    def stop(self):
        self._lock.acquire()
        self.stop_requested = True
        self._lock.release()
