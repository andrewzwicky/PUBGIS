import os

import cv2

from pubgis.minimap_iterators.generic import GenericIterator


class ImageIterator(GenericIterator):
    def __init__(self, folder, time_step, just_minimaps=False):
        super().__init__()
        images = [os.path.join(folder, img) for img in os.listdir(folder)]
        self.total = len(images)
        self.images = iter(images)
        self.count = 0
        self.just_minimaps = just_minimaps
        self.time_step = time_step
        first_image = cv2.imread(images[0])

        if self.just_minimaps:
            self.frame_index = slice(None)
            self.size = first_image.shape[0]
        else:
            self.frame_index = self.get_minimap_slice(*first_image.shape[0:2][::-1])

    def __iter__(self):
        return self

    def __next__(self):
        self.check_for_stop()

        img_path = next(self.images)
        timestamp = self.count * self.time_step
        self.count += 1

        return self.count * 100 / self.total, timestamp, cv2.imread(img_path)[self.frame_index]
