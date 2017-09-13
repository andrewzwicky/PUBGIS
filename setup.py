from distutils.core import setup

setup(name='PUBGIS',
      version='0.1',
      description='PUBG Location Tracker',
      author='Andrew Zwicky',
      url='https://github.com/andrewzwicky/PUBGIS',
      packages=['pubgis'],
      package_dir={'pubgis': 'pubgis'},
      package_data={'pubgis': ['images/*.jpg']}
      )
