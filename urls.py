#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Provides ``mapping`` of url paths to request handlers.
"""

from view import *

mapping = [(
        r'/', 
        Index
    ), (
        r'/standard', 
        Standard
    ), (
        r'/download', 
        Download
    ), (
        r'/library', 
        Library
    ), (
        r'/(.*)', 
        NotFound
    )
]
