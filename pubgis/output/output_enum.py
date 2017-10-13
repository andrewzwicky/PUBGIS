from enum import Flag, auto


class OutputFlags(Flag):
    NO_OUTPUT = 0
    LIVE_PREVIEW = auto()
    CROPPED_MAP = auto()
    FULL_MAP = auto()
    JSON = auto()
