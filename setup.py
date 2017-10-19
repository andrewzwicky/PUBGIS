from distutils.core import setup
from os.path import join, dirname

with open(join(dirname(__file__), 'pubgis', 'VERSION')) as version_file:
    version = version_file.read().strip()

with open('README.rst', 'r') as f:
    readme = f.read()

setup(name='PUBGIS',
      version=version,
      description='PUBG Location Tracker',
      long_description=readme,
      author='Andrew Zwicky',
      author_email='andrew.zwicky@gmail.com',
      license='GPLv3',
      url='https://github.com/andrewzwicky/PUBGIS',
      packages=['pubgis', 'pubgis.minimap_iterators'],
      package_dir={'pubgis': 'pubgis',
                   'pubgis.minimap_iterators': 'pubgis/minimap_iterators',
                   'pubgis.output': 'pubgis/output'},
      package_data={'pubgis': ['images/*.jpg', '*.ui', 'VERSION'],
                    '': ['LICENSE', 'README.md']},
      python_requires='>=3.6',
      install_requires=['numpy>=1.13.0+mkl',
                        'PyQt5>=5.9',
                        'opencv-python>=3.0',
                        'mss>=3.0.1',
                        'Pillow>=4.2.1',
                        'jsonschema>=2.6.0',
                        ],
      extras_require={
          'test': ['pytest>=3.2.2', 'pytest-profiling>=1.2.11']},
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
