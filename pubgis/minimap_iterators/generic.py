from threading import RLock

SUPPORTED_RESOLUTIONS = {(1920, 1080): (798, 1630, 251),
                         (2560, 1440): (1064, 2173, 335)}


class GenericIterator:
    def __init__(self):
        self.stop_requested = False
        self._lock = RLock()
        self.minimap_size = None

    def stop(self):
        with self._lock:
            self.stop_requested = True

    def check_for_stop(self):
        if self.stop_requested:
            raise StopIteration

    def get_minimap_bounds(self, width, height):
        try:
            x_offset, y_offset, size = SUPPORTED_RESOLUTIONS[(width, height)]
            self.minimap_size = size
            minimap_slice = (slice(x_offset, x_offset + self.minimap_size),
                             slice(y_offset, y_offset + self.minimap_size))

            return minimap_slice
        except KeyError:
            raise ResolutionNotSupportedException


class ResolutionNotSupportedException(Exception):
    pass
