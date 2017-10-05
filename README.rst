|icon| PUBGIS |Build status| |Github All Releases| |PyPI|
=========================================================

PUBGIS (PUBG Geographic Information System) analyzes gameplay from
`PUBG`_ (either live or video) and tracks your position during the game.
You can view this information later to see your path throughout the
game.

PUBGIS works by continuously scanning the minimap in the corner of the
game (seen below) and matching that to a location on the world map. If
you want more details about how PUBGIS works, check out the
`Implementation`_ wiki page

.. figure:: https://github.com/andrewzwicky/PUBGIS/raw/master/docs/minimap_callout_readme.jpg
   :scale: 80 %

Installation
------------

PUBGIS is a self-contained executable. Download the latest version
`here`_, no installation required!

Examples
--------

.. raw:: html

   <p align="center">

.. raw:: html

   </p>

Usage
-----

When PUBGIS is started, you'll see this:

.. raw:: html

   <p align="center">

.. raw:: html

   </p>

1. Select a video file (only tested with .mp4 currently)
2. Adjust the output file if needed.
3. Click Process!

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
.. _Implementation: https://github.com/andrewzwicky/PUBGIS/wiki/Implementation
.. _here: https://github.com/andrewzwicky/PUBGIS/releases/latest
.. _Development: https://github.com/andrewzwicky/PUBGIS/wiki/Development
.. _LICENSE.md: LICENSE.md

.. |icon| image:: pubgis/images/icons/navigation_32.png
.. |Build status| image:: https://ci.appveyor.com/api/projects/status/sbooipngsjk1kx46/branch/master?svg=true
   :target: https://ci.appveyor.com/project/andrewzwicky/pubgis/branch/master
.. |Github All Releases| image:: https://img.shields.io/github/downloads/andrewzwicky/PUBGIS/total.svg
   :target: https://github.com/andrewzwicky/PUBGIS/releases/latest
.. |PyPI| image:: https://img.shields.io/pypi/v/PUBGIS.svg
   :target: https://pypi.python.org/pypi/PUBGIS
