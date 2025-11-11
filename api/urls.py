from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('api/get-opcoes-turma/', views.get_opcoes_turma, name='get_opcoes_turma'),
    path('debug-log/', views.debug_log, name='debug_log'),
    path('api/get_materias_por_curso/', views.get_materias_por_curso, name='get_materias_por_curso'),
]