# ![icon](pubgis/images/icons/navigation_32.png) PUBGIS [![Build status](https://ci.appveyor.com/api/projects/status/sbooipngsjk1kx46/branch/master?svg=true)](https://ci.appveyor.com/project/andrewzwicky/pubgis/branch/master) [![Github All Releases](https://img.shields.io/github/downloads/andrewzwicky/PUBGIS/total.svg)](https://github.com/andrewzwicky/PUBGIS/releases/latest) [![PyPI](https://img.shields.io/pypi/v/PUBGIS.svg)](https://pypi.python.org/pypi/PUBGIS) 
 
PUBGIS (PUBG Geographic Information System) analyzes gameplay from [PUBG](https://www.playbattlegrounds.com/main.pu) (either live or video) and tracks your position during the game.  You can view this information later to see your path throughout the game.

PUBGIS works by continuously scanning the minimap in the corner of the game (seen below) and matching that to a location on the world map.  If you want more details about how PUBGIS works, check out the [Implementation](https://github.com/andrewzwicky/PUBGIS/wiki/Implementation) wiki page

<p align="center">
  <img src="docs\minimap_callout_readme.jpg" width="80%" align="top">
</p>


## Installation

PUBGIS is a self-contained executable.  Download the latest version [here](https://github.com/andrewzwicky/PUBGIS/releases/latest), no installation required!

## Examples

<p align="center">
  <img src="docs\example_path.jpg" height="400" align="top">
  <img src="docs\example_path_2.jpg" height="400" align="top">
  <img src="docs\example_path_3.jpg" height="400" align="top">
</p>

## Usage

When PUBGIS is started, you'll see this:
<p align="center">
  <img src="docs\example_setup.jpg" width="45%">
</p>

1. Select a video file (only tested with .mp4 currently)
2. Adjust the output file if needed.
3. Click Process!

**Optional**:
* If the video contains extra footage *before your parachute landing*, put that time in **landing time**
* If the video contains extra footage *after you die*, such as spectating a teammate, input your **death time** (death time of 00:00 means it will process until the end of the video)
* Adjust the time step.  This is how often the map is checked.  Larger values will process a game faster, but the path will not be as detailed.
* Select a different color path


## Development

PUBGIS is written in Python (3.6).  If you'd like to use PUBGIS as a python package, you can install it using `pip`

    pip install pubgis

and run it using:

    python -m pubgis

To learn more about extending or contributing to PUBGIS, check out the [Development](https://github.com/andrewzwicky/PUBGIS/wiki/Development) page.

## License

This project is licensed under the GPLv3 License - see the [LICENSE.md](LICENSE.md) file for details
