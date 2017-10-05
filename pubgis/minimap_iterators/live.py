import time

import mss
import numpy as np

from pubgis.minimap_iterators.generic import GenericIterator


class LiveFeed(GenericIterator):
    def __init__(self, time_step, monitor):
        super().__init__()
        self.monitor = monitor
        self.time_step = time_step
        self.time = time.time()

        with mss.mss() as sct:
            self.frame_index = self.get_minimap_bounds(sct.monitors[self.monitor]['width'],
                                                       sct.monitors[self.monitor]['height'])

    def __iter__(self):
        return self

    def __next__(self):
        self.check_for_stop()

        time.sleep(max(0, self.time_step - (time.time() - self.time)))

        with mss.mss() as sct:
            frame = np.array(sct.grab(sct.monitors[self.monitor]))
        minimap = frame[self.frame_index][:, :, :3]
        minimap = minimap.copy()

        self.time = time.time()
        return None, minimap
