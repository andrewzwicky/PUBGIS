import time

import mss
import numpy as np

from pubgis.minimap_iterators.generic import GenericIterator


class LiveFeed(GenericIterator):
    def __init__(self, time_step, monitor):
        super().__init__()
        self.monitor = monitor
        self.time_step = time_step
        self.sct = mss.mss()
        self.last_execution_time = None
        self.begin_time = None

        y_offset, x_offset, size = self.get_minimap_bounds(
            self.sct.monitors[self.monitor]['width'],
            self.sct.monitors[self.monitor]['height'])

        self.minimap_bounds = {'top': y_offset + self.sct.monitors[self.monitor]['top'],
                               'left': x_offset + self.sct.monitors[self.monitor]['left'],
                               'width': size,
                               'height': size}

    def __iter__(self):
        return self

    def __next__(self):
        self.check_for_stop()

        if self.last_execution_time is None or self.begin_time is None:
            self.last_execution_time = self.begin_time = time.time()
        else:
            # only want to sleep enough time to create the time_step between start of executions
            # If that time has already been exceeded, don't sleep at all
            time.sleep(max(0, self.time_step - (time.time() - self.last_execution_time)))
            self.last_execution_time = time.time()

        minimap = np.array(self.sct.grab(self.minimap_bounds))

        return None, self.last_execution_time - self.begin_time, minimap
