# PUBGIS
[![Build Status](https://travis-ci.org/andrewzwicky/PUBGIS.svg?branch=master)](https://travis-ci.org/andrewzwicky/PUBGIS)

PUBGIS (PUBG Geographic Information System) is a python program that generates player paths through the PUBG map from gameplay footage.

## Examples

<p align="center">
  <img src="docs\example_path.jpg" width="33%">
  <img src="docs\example_path_2.jpg" width="33%">
  <img src="docs\example_path_3.jpg" width="33%">
</p>

## Functionality

PUBGIS first determines whether the minimap is actually being displayed in the correct position by checking for the player indicator.  Currently, this is done by masking everything except the area where the indicator should be, then checking the mean color.  If this mean color is within the acceptable range (basically white/light gray), then it's assumed that the minimap is up.

 PUBGIS then uses template matching to attempt to match the minimap with the correct section on the full map.  This technique "slides" the template image across the full image, comparing the matches at each point.  The best match that above the acceptability threshold is selected, and the coordinates are calculated from the location.


## Installation


## Usage

From within the PUBGIS folder, run:

    pubgis -m pubgis

to bring up the GUI.

## Limitations

PUBGIS has some shortcomings right now:
* PUBGIS relies on viewing the minimap frequently, so if you have the full map open for extended time (i.e. passenger in a vehicle), PUBGIS may not be able to find your position during that time.
* Currently, the minimap location is only set up for 1920x1080 video.
