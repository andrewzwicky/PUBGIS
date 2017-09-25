# ![icon](pubgis/images/icons/navigation_64.png) PUBGIS [![Build status](https://ci.appveyor.com/api/projects/status/sbooipngsjk1kx46?svg=true)](https://ci.appveyor.com/project/andrewzwicky/pubgis)

PUBGIS (PUBG Geographic Information System) is a python program that generates player paths through the PUBG map from gameplay footage.

## Examples

<p align="center">
  <img src="docs\example_path.jpg" width="33%">
  <img src="docs\example_path_2.jpg" width="33%">
  <img src="docs\example_path_3.jpg" width="33%">
</p>

## Installation

    pip install pubgis

## Usage

    python -m pubgis

will bring up the GUI.  From there, you can select your video file and start processing it.

<p align="center">
  <img src="docs\example_setup.jpg" width="45%">
  <img src="docs\example_processing.jpg" width="45%">
</p>

## Functionality

PUBGIS first determines whether the minimap is actually being displayed in the correct position by checking for the player indicator.  Currently, this is done by masking everything except the area where the indicator should be, then checking the mean color.  If this mean color is within the acceptable range (basically white/light gray), then it's assumed that the minimap is up.

 PUBGIS then uses template matching to attempt to match the minimap with the correct section on the full map.  This technique "slides" the template image across the full image, comparing the matches at each point.  The best match that above the acceptability threshold is selected, and the coordinates are calculated from the location.

## Limitations

PUBGIS has some shortcomings right now:
* PUBGIS relies on viewing the minimap frequently, so if you have the full map open for extended time (i.e. passenger in a vehicle), PUBGIS may not be able to find your position during that time.
* Currently, the minimap location is only set up for 1920x1080 video.

## License

This project is licensed under the GPLv3 License - see the [LICENSE.md](LICENSE.md) file for details
