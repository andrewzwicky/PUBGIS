import cv2

from pubgis.minimap_iterators.generic import GenericIterator

DEFAULT_STEP_INTERVAL = 1


class VideoIterator(GenericIterator):
    def __init__(self,
                 video_file=None,
                 landing_time=0,
                 time_step=DEFAULT_STEP_INTERVAL,
                 death_time=None, ):
        super().__init__()
        self.cap = cv2.VideoCapture(video_file)
        self.frame_index = self.get_minimap_bounds(int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                                   int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.landing_frame = int(landing_time * self.fps)
        self.time_step = time_step
        self.step_frames = max(int(time_step * self.fps), 1) - 1
        # TODO: assert death time > landing_time
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
