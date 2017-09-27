# ![icon](pubgis/images/icons/navigation_32.png) PUBGIS [![Build status](https://ci.appveyor.com/api/projects/status/sbooipngsjk1kx46?svg=true)](https://ci.appveyor.com/project/andrewzwicky/pubgis)

PUBGIS (PUBG Geographic Information System) analyzes gameplay from [PUBG](https://www.playbattlegrounds.com/main.pu) (either live or video) and tracks your position during the game.  You can view this information later to see your path throughout the game.

PUBGIS works by continuously polling the minimap in the corner of the game (seen below) and matching that to a location on the world map.  If you want more details about how PUBGIS works, check out the [Implementation](https://github.com/andrewzwicky/PUBGIS/wiki/Implementation) wiki page

<p align="center">
  <img src="docs\example_minimap.jpg" width="45%">
  <img src="docs\example_minimap_location.jpg" width="45%">
</p>

## Installation

To run PUBGIS, download the latest executable [here](https://github.com/andrewzwicky/PUBGIS/releases/latest).  That's it, there's no dependencies or installation process.

## Examples

<p align="center">
  <img src="docs\example_path.jpg" width="33%" align="top">
  <img src="docs\example_path_2.jpg" width="33%" align="top">
  <img src="docs\example_path_3.jpg" width="33%" align="top">
</p>

## Usage

When PUBGIS is started, you'll see this:
<p align="center">
  <img src="docs\example_setup.jpg" width="45%">
</p>

## Development

PUBGIS is written in Python (3.6).  If you'd like to use PUBGIS as a python package, you can install it using `pip`

    pip install pubgis

and run it using:

    python -m pubgis

To learn more about extending or contributing to PUBGIS, check out the [Development](https://github.com/andrewzwicky/PUBGIS/wiki/Development) page.

## License

This project is licensed under the GPLv3 License - see the [LICENSE.md](LICENSE.md) file for details
