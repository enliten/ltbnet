#!/usr/bin/env python

from setuptools import setup

setup(name='ltbnet',
      version='0.1.2',
      description='LTB PMU Data Streaming Network based on Mininet',
      author=['Hantao Cui'],
      author_email='cuihantao@gmail.com',
      url='https://cuihantao.github.io/',
      packages=['ltbnet'],
      entry_points={
          'console_scripts': [
              'ltbnet = ltbnet.main:main',
              'minipmu = ltbnet.minipmu:main',
          ]
      },
      )
