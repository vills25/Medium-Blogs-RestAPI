# """
# WSGI config for medium_blog_api_project project.

# It exposes the WSGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
# """

# import os

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medium_blog_api_project.settings')

# application = get_wsgi_application()

import sys
import os

project_home = '/home/VishalSohaliyaMediCenter/Medium-Blogs-RestAPI'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['DJANGO_SETTINGS_MODULE'] = 'medium_blog_api_app.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
