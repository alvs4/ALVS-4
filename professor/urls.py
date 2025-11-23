from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    # DASHBOARD
    path('professor/dashboard/', views.professor_dashboard_view, name='professor_dashboard'),
    
    # BOTÃO
    path('professor/materia/<int:materia_id>/turma/<int:turma_id>/', views.detalhar_turma_professor, name='detalhar_turma_professor'),
    
    # MATÉRIAS-ANO-CURSO-MODALIDADE-ESTÁGIO
    path('professor/materia/<int:materia_id>/turma/<int:turma_id>/', views.ver_turma_professor, name='ver_turma_professor'),
    path('professor/vinculo/<int:vinculo_id>/turmas/', views.listar_turmas_vinculadas, name='listar_turmas_vinculadas'),
    path('professor/aluno/<int:aluno_id>/detalhes/', views.ver_detalhes_aluno_professor, name='ver_detalhes_aluno_professor'),
    path('professor/estagio/documento/<int:documento_id>/visualizar/', views.professor_visualizar_documento, name='professor_visualizar_documento'),
    path('professor/estagio/documento/<int:documento_id>/assinar/', views.professor_assinar_documento, name='professor_assinar_documento'),
    path('documento/<int:documento_id>/preencher/', views.professor_preencher_documento, name='professor_preencher_documento'),
]