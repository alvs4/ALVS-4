from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # DASHBOARD
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),

    # BOTÕES
    path('admin/professor_crud/professores/', views.gerenciar_professores, name='gerenciar_professores'),
    path('admin/aluno_crud/alunos/', views.gerenciar_alunos, name='gerenciar_alunos'),
    path('admin/servidores/', views.gerenciar_servidores, name='gerenciar_servidores'),
    path('admin/materias_crud/materias/', views.listar_materias, name='listar_materias'),
    path('admin/turmas_crud/turmas/', views.listar_turmas, name='listar_turmas'),
    
    # CRUD - PROFESSOR
    path('admin/professor_crud/professores/novo/', views.cadastrar_professor, name='cadastrar_professor'),
    path('admin/professor_crud/professores/<int:professor_id>/ver/', views.ver_detalhes_professor, name='ver_detalhes_professor'),
    path('admin/professor_crud/professores/<int:professor_id>/editar/', views.editar_professor, name='editar_professor'),
    path('admin/professor_crud/professores/<int:professor_id>/remover/', views.remover_professor, name='remover_professor'),
    
    # CRUD - ALUNO
    path('admin/aluno_crud/alunos/novo/', views.cadastrar_aluno, name='cadastrar_aluno'),
    path('admin/aluno_crud/alunos/<int:aluno_id>/editar/', views.editar_aluno, name='editar_aluno'),
    path('admin/aluno_crud/alunos/<int:aluno_id>/remover/', views.remover_aluno, name='remover_aluno'),
    path('admin/aluno_crud/alunos/<int:aluno_id>/ver/', views.ver_detalhes_aluno, name='ver_detalhes_aluno'),
    
    # CRUD - SERVIDOR
    path('admin/servidores/novo/', views.cadastrar_servidor, name='cadastrar_servidor'),
    path('admin/servidores/<int:servidor_id>/ver/', views.ver_detalhes_servidor, name='ver_detalhes_servidor'),
    path('admin/servidores/<int:servidor_id>/editar/', views.editar_servidor, name='editar_servidor'),
    path('admin/servidores/<int:servidor_id>/remover/', views.remover_servidor, name='remover_servidor'),
    
    # CRUD - MATERIA
    path('admin/materias_crud/cursos/<int:curso_id>/materias/', views.listar_materias_por_curso, name='listar_materias_por_curso'),
    path('admin/materias_crud/materias/<int:materia_id>/', views.detalhar_materia, name='detalhar_materia'),
    
    # CRUD - TURMA
    path('admin/turmas_crud/cursos/<int:curso_id>/turmas/', views.listar_turmas_por_curso, name='listar_turmas_por_curso'),
    path('admin/turmas_crud/turmas/<int:turma_id>/', views.detalhar_turma, name='detalhar_turma'),
]