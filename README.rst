|icon| PUBGIS |Build status| |Github All Releases| |PyPI|
=========================================================

PUBGIS (PUBG Geographic Information System) analyzes gameplay from
`PUBG`_ (either live or video) and tracks your position during the game.
You can view this information later to see your path throughout the
game.

PUBGIS works by continuously scanning the minimap in the corner of the
game (seen below) and matching that to a location on the world map. If
you want more details about how PUBGIS works, check out the
`Theory_of_Operation`_ wiki page

Installation
------------

PUBGIS is a self-contained executable. Download the latest version
`here`_, no installation required!

Examples
--------

.. image:: https://github.com/andrewzwicky/PUBGIS/raw/master/docs/composite_example.png

Usage
-----

When PUBGIS is started, you'll see this:

.. figure:: https://github.com/andrewzwicky/PUBGIS/raw/master/docs/example_setup.jpg
   :scale: 45 %

1a. Select a video file (only tested with .mp4 currently)

1b. Click the Live tab to record as you play.

2. Adjust the output file if needed.

3. Click Process!

**NOTE:**  PUBGIS live recording does not currently work when running PUBG Fullscreen (Fullscreen (Windowed) is OK). I'm tracking `Issue#41`_. Sorry for the inconvenience.

**Optional**:

* If the video contains extra footage *before your parachute landing*, put that time in **landing time**

* If the video contains extra footage *after you die*, such as spectating a teammate, input your **death time** (death time of 00:00 means it will process until the end of the video)

* Adjust the time step. This is how often the map is checked. Larger values will process a game faster, but the path will not be as detailed.

* Select a different color path

Development
-----------

PUBGIS is written in Python (3.6). If you'd like to use PUBGIS as a
python package, you can install it using ``pip``

::

    pip install pubgis

and run it using:

::

    python -m pubgis

To learn more about extending or contributing to PUBGIS, check out the
`Development`_ page.

License
-------

This project is licensed under the GPLv3 License - see the `LICENSE.md`_
file for details

.. _PUBG: https://www.playbattlegrounds.com/main.pu
.. _Theory_of_Operation: https://github.com/andrewzwicky/PUBGIS/wiki/Theory-of-Operation
.. _here: https://github.com/andrewzwicky/PUBGIS/releases/latest
.. _Issue#41: https://github.com/andrewzwicky/PUBGIS/releases/latest
.. _Development: https://github.com/andrewzwicky/PUBGIS/wiki/Development
.. _LICENSE.md: LICENSE.md

.. |icon| image:: pubgis/images/icons/navigation_32.png
.. |Build status| image:: https://ci.appveyor.com/api/projects/status/sbooipngsjk1kx46/branch/master?svg=true
   :target: https://ci.appveyor.com/project/andrewzwicky/pubgis/branch/master
.. |Github All Releases| image:: https://img.shields.io/github/downloads/andrewzwicky/PUBGIS/total.svg
   :target: https://github.com/andrewzwicky/PUBGIS/releases/latest
.. |PyPI| image:: https://img.shields.io/pypi/v/PUBGIS.svg
   :target: https://pypi.python.org/pypi/PUBGIS
