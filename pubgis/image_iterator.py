import os
from threading import RLock

import cv2


class ImageIterator:
    def __init__(self, folder):
        images = [os.path.join(folder, img) for img in os.listdir(folder)]
        self.total = len(images)
        self.images = iter(images)
        self.count = 0
        self._lock = RLock()

    def __iter__(self):
        return self

    def __next__(self):
        self._lock.acquire()
        img_path = next(self.images)
        self.count += 1
        self._lock.release()
        return self.count*100/self.total, cv2.imread(img_path)
