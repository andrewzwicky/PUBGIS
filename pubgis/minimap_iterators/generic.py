from threading import RLock

SUPPORTED_RESOLUTIONS = {(1920, 1080): (slice(798, 798+253), slice(1630, 1630+252))}


class GenericIterator:
    def __init__(self):
        self.stop_requested = False
        self._lock = RLock()

    def stop(self):
        with self._lock:
            self.stop_requested = True

    def check_for_stop(self):
        if self.stop_requested:
            raise StopIteration

    @staticmethod
    def get_minimap_bounds(width, height):
        try:
            return SUPPORTED_RESOLUTIONS[(width, height)]
        except KeyError:
            raise ResolutionNotSupportedException


class ResolutionNotSupportedException(Exception):
    pass
