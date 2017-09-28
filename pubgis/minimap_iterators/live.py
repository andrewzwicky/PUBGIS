import mss
import numpy as np

from pubgis.minimap_iterators.generic import GenericIterator


class LiveFeed(GenericIterator):  # pylint: disable=no-self-use
    def __init__(self, monitor=1):
        super().__init__()
        self.monitor = monitor

        with mss.mss() as sct:
            self.frame_index = self.get_minimap_bounds(sct.monitors[self.monitor]['width'],
                                                       sct.monitors[self.monitor]['height'])

    def __iter__(self):
        return self

    def __next__(self):
        self.check_for_stop()

        with mss.mss() as sct:
            frame = np.array(sct.grab(sct.monitors[self.monitor]))
        minimap = frame[self.frame_index][:, :, :3]
        minimap = minimap.copy()
        return None, minimap
