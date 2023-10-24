import os

# set environment from variable
environment = os.environ.get('ENVIRONMENT')

if environment == 'development':
    from example_project.settings.development import *
elif environment == 'testing':
    from example_project.settings.testing import *
elif environment == 'acceptance':
    from example_project.settings.acceptance import *
elif environment == 'production':
    from example_project.settings.production import *
else:
    from example_project.settings.development import *