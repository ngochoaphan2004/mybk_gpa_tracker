"""
WSGI config for gpa_web project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpa_web.settings')

application = get_wsgi_application()

# BẮT BUỘC PHẢI CÓ DÒNG NÀY CHO VERCEL
app = application