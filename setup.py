from setuptools import setup

setup (
   name = 'masterflex',
   version = '0.1',
   description = 'Python library for Masterflex L/S pumps',
   license='MIT',
   author = 'Camille Kim',
   author_email = 'ykim@middlebury.edu',
   platforms = 'any',
   packages = ['masterflex'],
   install_requires = ['python 2.7', 'pyserial 2.7']
)