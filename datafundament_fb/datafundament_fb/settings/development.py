"""
Settings for a development environment
"""

from pathlib import Path
import os

# Load the default settings from base.py
from datafundament_fb.settings.base import *

# Settings specific to this enviromnent
INSTALLED_APPS += [
    'django_extensions',
]