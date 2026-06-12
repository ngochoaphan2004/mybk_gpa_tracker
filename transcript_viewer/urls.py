from django.urls import path
from . import views

urlpatterns = [
    path('', views.transcript_view, name='transcript_view'),
]
