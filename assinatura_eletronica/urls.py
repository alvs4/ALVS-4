from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('verificar/<uuid:codigo_uuid>/', views.verificar_documento_publico, name='verificar_documento_publico'),
]