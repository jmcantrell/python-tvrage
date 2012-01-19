#!/usr/bin/env python

from setuptools import setup

setup(
        name='tvrage',
        version='0.1.1',
        description='Python interface to the TVRage television information database.',
        author='Jeremy Cantrell',
        author_email='jmcantrell@gmail.com',
        classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: BSD License',
            'Natural Language :: English',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            ],
        install_requires=[
            'lxml',
            ],
        py_modules=[
            'tvrage',
            ],
        )
