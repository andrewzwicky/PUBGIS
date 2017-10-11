import os

with open(os.path.join('VERSION')) as version_file:
    __version__ = version_file.read().strip()
