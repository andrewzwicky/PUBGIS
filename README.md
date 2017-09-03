# PUBGIS

PUBGIS (PUBG Geographic Information System) is a python program that generates player paths through the PUBG map from gameplay footage.

![example](./example_path.png)

## Functionality

PUBGIS first determines whether the minimap is actually being displayed in the correct position by checking for the player indicator.  Currently, this is done by masking everything except the area where the indicator should be, then checking the mean color.  If this mean color is within the acceptable range (basically white/light gray), then it's assumed that the minimap is up.

 PUBGIS then uses template matching to attempt to match the minimap with the correct section on the full map.  This technique "slides" the template image across the full image, comparing the matches at each point.  The best match that above the acceptability threshold is selected, and the coordinates are calculated from the location.

## Examples


## Installation


## Usage

To see available arguments type:

    pubgis --help


## Limitations

PUBGIS has some shortcomings right now:
* Currently the minimap markers display on top of the player indicator, so this can lead to some false negatives
* PUBGIS relies on viewing the minimap frequently, so if you have the full map open for extended time (i.e. passenger in a vehicle), PUBGIS may not be able to find your position during that time.
