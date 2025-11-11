from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    # DASHBOARD
    path('aluno/dashboard/', views.aluno_dashboard_view, name='aluno_dashboard'),
    
    # ESTÁGIO
    path('aluno/estagio/', views.gestao_estagio_aluno, name='solicitar_estagio'),
    path('aluno/estagio/detalhes/', views.detalhes_estagio_aluno, name='detalhes_estagio_aluno'),
    path('aluno/estagio/documento/<int:documento_id>/visualizar/', views.visualizar_documento_estagio, name='visualizar_documento_estagio'),
    path('aluno/estagio/documento/<int:documento_id>/preencher/', views.preencher_documento_estagio, name='preencher_documento_estagio'),
    path('aluno/estagio/documento/<int:documento_id>/upload-pdf/', views.upload_pdf_assinado, name='upload_pdf_assinado'),
    path('aluno/estagio/documento/<int:documento_id>/remover_pdf/', views.remover_pdf_assinado, name='remover_pdf_assinado'),
    path('aluno/estagio/documento/<int:documento_id>/assinar/', views.assinar_documento_aluno, name='assinar_documento_aluno'),
]