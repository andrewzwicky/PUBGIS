from threading import RLock

SUPPORTED_RESOLUTIONS = {(1280, 720): (532, 1087, 167),
                         (1366, 768): (568, 1158, 178),
                         (1600, 900): (665, 1358, 209),
                         (1680, 1050): (776, 1398, 244),
                         (1920, 1080): (798, 1630, 251),
                         (1920, 1200): (886, 1597, 280),
                         (2560, 1440): (1064, 2173, 335),
                         (3440, 1440): (1064, 3053, 335)}


class GenericIterator:
    def __init__(self):
        self.stop_requested = False
        self.size = None
        self.time_step = None

    def stop(self):
        self.stop_requested = True

    def check_for_stop(self):
        if self.stop_requested:
            raise StopIteration

    def get_minimap_bounds(self, width, height):
        try:
            x_offset, y_offset, size = SUPPORTED_RESOLUTIONS[(width, height)]
            self.size = size
            minimap_slice = (slice(x_offset, x_offset + self.size),
                             slice(y_offset, y_offset + self.size))

            return minimap_slice
        except KeyError:
            raise ResolutionNotSupportedException


class ResolutionNotSupportedException(Exception):
    pass
