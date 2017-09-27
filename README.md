# ![icon](pubgis/images/icons/navigation_32.png) PUBGIS [![Build status](https://ci.appveyor.com/api/projects/status/sbooipngsjk1kx46?svg=true)](https://ci.appveyor.com/project/andrewzwicky/pubgis)

PUBGIS (PUBG Geographic Information System) analyzes gameplay from [PUBG](https://www.playbattlegrounds.com/main.pu) (either live or recorded) and provides a plot of your player position throughout the course of the game.

PUBGIS works by continuously polling the minimap in the corner of the game (seen below) and matching that to a location on the world map.  If you want more details about how PUBGIS works, check out the [Implementation](https://github.com/andrewzwicky/PUBGIS/wiki/Implementation) wiki page

<p align="center">
  <img src="docs\example_minimap.jpg" width="50%">
</p>

## Examples

<p align="center">
  <img src="docs\example_path.jpg" width="33%">
  <img src="docs\example_path_2.jpg" width="33%">
  <img src="docs\example_path_3.jpg" width="33%">
</p>

## Installation

To run PUBGIS, download the latest executable [here](https://github.com/andrewzwicky/PUBGIS/releases/latest).  That's it, there's no dependencies or installation process.

## Usage

When PUBGIS is started, you'll see this:
<p align="center">
  <img src="docs\example_setup.jpg" width="45%">
</p>

## Development

PUBGIS is written in Python 3.6.  If you'd like to use PUBGIS as a python package, you can install it using `pip`

    pip install pubgis

and run it using:

    python -m pubgis

To learn more about extending or contributing to PUBGIS, check out the [Development](https://github.com/andrewzwicky/PUBGIS/wiki/Development) page.

## Functionality

PUBGIS first determines whether the minimap is actually being displayed in the correct position by checking for the player indicator.  Currently, this is done by masking everything except the area where the indicator should be, then checking the mean color.  If this mean color is within the acceptable range (basically white/light gray), then it's assumed that the minimap is up.

 PUBGIS then uses template matching to attempt to match the minimap with the correct section on the full map.  This technique "slides" the template image across the full image, comparing the matches at each point.  The best match that above the acceptability threshold is selected, and the coordinates are calculated from the location.

## Limitations

PUBGIS has some shortcomings right now:
* PUBGIS relies on viewing the minimap frequently, so if you have the full map open for extended time (i.e. passenger in a vehicle), PUBGIS may not be able to find your position during that time.
* Currently, the minimap location is only set up for 1920x1080 video.

## License

This project is licensed under the GPLv3 License - see the [LICENSE.md](LICENSE.md) file for details
