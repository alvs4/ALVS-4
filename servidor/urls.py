from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    # DASHBOARD
    path('servidor/dashboard/', views.servidor_dashboard_view, name='servidor_dashboard'),
    
    # ESTÁGIO
    path('servidor/monitorar/', views.servidor_monitorar_alunos, name='servidor_monitorar_alunos'),
    path('servidor/aluno/<int:aluno_id>/documentos/', views.servidor_ver_documentos_aluno, name='servidor_ver_documentos_aluno'),
    path('direcao/documento/<int:documento_id>/assinar/', views.direcao_assinar_documento, name='direcao_assinar_documento'),
    path('direcao/documento/<int:documento_id>/visualizar/', views.direcao_visualizar_documento, name='direcao_visualizar_documento'),
    path('servidor/documento/<int:documento_id>/visualizar/', views.servidor_visualizar_documento, name='servidor_visualizar_documento'),
    path('servidor/documento/<int:documento_id>/aprovar/', views.servidor_aprovar_documento, name='servidor_aprovar_documento'),
    path('servidor/documento/<int:documento_id>/reprovar/', views.servidor_reprovar_documento, name='servidor_reprovar_documento'),
]