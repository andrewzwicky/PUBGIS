from pubgis.match import MMAP_HEIGHT, MMAP_WIDTH, MMAP_X, MMAP_Y
import cv2

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
            self.death_frame = int(death_time * fps)
        else:
            self.death_frame = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frames_processed = 0
        self.frames_to_process = self.death_frame - self.landing_frame
        self.initialized = False

    def __iter__(self):
        for _ in range(self.landing_frame):
            self.cap.grab()
        return self

    def __next__(self):
        grabbed, frame = self.cap.read()
        self.frames_processed += 1

        if grabbed:
            if frame.shape == (1080, 1920, 3):
                minimap = frame[MMAP_Y:MMAP_Y + MMAP_HEIGHT, MMAP_X:MMAP_X + MMAP_WIDTH]
            else:
                raise ValueError("Only 1920x1800 video is supported at this time.")

            percent = min(int((self.frames_processed / self.frames_to_process) * 100), 100)

            for _ in range(self.step_frames):
                self.cap.grab()
            self.frames_processed += self.step_frames

            return percent, minimap
        else:
            raise StopIteration
