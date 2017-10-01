from distutils.core import setup
from setuptools import find_packages

setup(name='PUBGIS',
      version='0.1.4',
      description='PUBG Location Tracker',
      author='Andrew Zwicky',
      author_email='andrew.zwicky@gmail.com',
      license='GPLv3',
      url='https://github.com/andrewzwicky/PUBGIS',
      packages=find_packages(),
      package_dir={'pubgis': 'pubgis'},
      package_data={'pubgis': ['images/*.jpg']},
      python_requires='>=3.6',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: X11 Applications :: Qt',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Topic :: Games/Entertainment :: First Person Shooters',
          'Topic :: Multimedia :: Graphics :: Capture :: Screen Capture',
          'Topic :: Multimedia :: Video :: Capture',
          'Topic :: Utilities',
          'Programming Language :: Python :: 3.6',
      ]
      )
