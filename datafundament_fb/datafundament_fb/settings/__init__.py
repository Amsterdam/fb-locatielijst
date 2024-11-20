import os

# set environment from variable
environment = os.environ.get('ENVIRONMENT')

if environment == 'local':
    from datafundament_fb.settings.local import *
elif environment == 'development':
    from datafundament_fb.settings.development import *
elif environment == 'testing':
    from datafundament_fb.settings.testing import *
elif environment == 'acceptance':
    from datafundament_fb.settings.acceptance import *
elif environment == 'production':
    from datafundament_fb.settings.production import *
else:
    from datafundament_fb.settings.base import *