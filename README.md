# PUBGIS

PUBGIS is a program to generate player paths in PUBG from gameplay video.  PUBG currently does not have any player pathing functionality, so PUBGIS can fill this gap until that functionality is present.

## How does it work?

PUBGIS uses python and opencv to analyze gameplay videos by extracting the minimap from the frames of the video at regular intervals. The frames are then matched with the correct section of the full map, thus determining the player location.

The minimap is compared against the full map using template matching.  This technique "slides" the template image across the full image, comparing the matches at each point.  The best match is selected to use as the coordinates

To reduce false positives, there is a threshold for the match that must be exceeded.  As well, there is a check to make sure the player indicator is present as well (to prevent matches when the player is viewing the full map on their screen).

## Limitations

* Currently, I've only tested with 1920x1080 video
* Player markers appear over the player indicator on the map, this can sometimes cause the