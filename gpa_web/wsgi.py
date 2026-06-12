import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpa_web.settings')

application = get_wsgi_application()

# BẮT BUỘC PHẢI CÓ DÒNG NÀY ĐỂ VERCEL NHẬN DIỆN ENTRY POINT
app = application