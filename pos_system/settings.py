"""
Django settings loader for pos_system project.
Load appropriate settings based on DJANGO_ENV environment variable.
"""

import os

# Determine which settings to use
ENVIRONMENT = os.environ.get('DJANGO_ENV', 'development')

if ENVIRONMENT == 'production':
    from .settings_prod import *
elif ENVIRONMENT == 'development':
    from .settings_dev import *
else:
    # Default to development settings
    from .settings_dev import *