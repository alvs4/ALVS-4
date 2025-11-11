from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Curso, Turma, Materia, 
    ProfessorMateriaAnoCursoModalidade, AlunoTurma, 
    Nota, Estagio, DocumentoEstagio
)

# --- Configurações para melhorar a exibição no Admin ---

class CustomUserAdmin(UserAdmin):
    """
    Personaliza a exibição do CustomUser no Admin.
    """
    model = CustomUser
    # Campos que aparecem na lista de usuários
    list_display = ['username', 'email', 'first_name', 'last_name', 'tipo']
    # Filtros que aparecem na lateral
    list_filter = ['tipo', 'eixo', 'is_staff']
    # Campos que o Admin pode usar para buscar
    search_fields = ['username', 'first_name', 'last_name', 'email']
    
    # Adiciona os campos 'tipo', 'eixo', etc., na tela de edição do usuário
    # (Isto é importante para o Admin poder ver e editar tudo)
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Customizadas', {
            'fields': ('tipo', 'eixo', 'numero_matricula', 'cpf', 'rg', 
                       'data_nascimento', 'telefone')
        }),
    )

class EstagioAdmin(admin.ModelAdmin):
    """
    Personaliza a exibição dos Dossiês de Estágio.
    Esta é a configuração que você precisa para corrigir o problema.
    """
    # Campos que aparecem na lista de estágios
    list_display = ('aluno', 'orientador', 'status_geral', 'supervisor_empresa')
    # Filtros na lateral
    list_filter = ('status_geral', 'orientador')
    # Campos de busca
    search_fields = ('aluno__first_name', 'aluno__last_name', 'supervisor_empresa')
    
    # IMPORTANTE: Permite que você procure/selecione alunos e orientadores
    autocomplete_fields = ['aluno', 'orientador']

class TurmaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'curso', 'ano_modulo', 'turno', 'modalidade')
    list_filter = ('curso__eixo', 'curso', 'ano_modulo', 'turno', 'modalidade')
    search_fields = ('curso__nome',) # Habilita a busca para o autocomplete

class AlunoTurmaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'turma', 'ano_letivo')
    search_fields = ('aluno__first_name', 'turma__curso__nome')
    autocomplete_fields = ['aluno', 'turma'] # Facilita a busca

# --- REGISTRO DOS MODELOS ---
# (Isto é o que faz eles aparecerem na tela)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Curso)
admin.site.register(Turma, TurmaAdmin)
admin.site.register(Materia)
admin.site.register(ProfessorMateriaAnoCursoModalidade)
admin.site.register(AlunoTurma, AlunoTurmaAdmin)
admin.site.register(Nota)
admin.site.register(Estagio, EstagioAdmin) # <-- O mais importante para você agora
admin.site.register(DocumentoEstagio)