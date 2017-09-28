import os
from threading import RLock

import cv2
from pubgis.minimap_iterators.generic import GenericIterator


class ImageIterator(GenericIterator):
    def __init__(self, folder):
        super().__init__()
        self.total = len(images)
        self.images = iter([os.path.join(folder, img) for img in os.listdir(folder)])
        self.count = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.check_for_stop()

        with self._lock:
            img_path = next(self.images)
            self.count += 1
            return self.count*100/self.total, cv2.imread(img_path)
