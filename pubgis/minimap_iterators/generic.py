SUPPORTED_RESOLUTIONS = \
    {
        #(1280, 720): (532, 1087, 167),
        #(1366, 768): (568, 1158, 178),
        #(1600, 900): (665, 1358, 209),
        #(1680, 1050): (776, 1398, 244),
        (1920, 1080): (796, 1628, 255),
        #(1920, 1200): (886, 1597, 280),
        #(2560, 1440): (1064, 2173, 335),
        #(3440, 1440): (1064, 3053, 335)
    }


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
            y_offset, x_offset, size = SUPPORTED_RESOLUTIONS[(width, height)]
            self.size = size
            return y_offset, x_offset, size
        except KeyError:
            raise ResolutionNotSupportedException

    def get_minimap_slice(self, width, height):
        y_offset, x_offset, size = self.get_minimap_bounds(width, height)
        minimap_slice = (slice(y_offset, y_offset + size),
                         slice(x_offset, x_offset + size))

        return minimap_slice


class ResolutionNotSupportedException(Exception):
    pass
