from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Curso, Turma, Materia, 
    ProfessorMateriaAnoCursoModalidade, AlunoTurma,
    Estagio, DocumentoEstagio
)

# --- Configurações para melhorar a exibição no Admin ---

class CustomUserAdmin(UserAdmin):
    """
    Personaliza a exibição do CustomUser no Admin.
    """
    model = CustomUser

    # Campos que aparecem na lista de usuários
    list_display = ['username', 'email', 'first_name', 'last_name', 'tipo', 
                    'email_confirmado', 'dois_fatores_email', 'usa_google_authenticator']

    # Filtros
    list_filter = ['tipo', 'eixo', 'email_confirmado', 'dois_fatores_email', 'usa_google_authenticator']

    search_fields = ['username', 'first_name', 'last_name', 'email']

    fieldsets = UserAdmin.fieldsets + (
        ('Informações Customizadas', {
            'fields': (
                'tipo', 'eixo', 'numero_matricula', 'cpf', 'rg',
                'data_nascimento', 'telefone',
            )
        }),
        ('Segurança e 2FA', {
            'fields': (
                'email_confirmado',
                'dois_fatores_email',
                'usa_google_authenticator',
                'secret_2fa',
            )
        }),
    )

    readonly_fields = ['secret_2fa']  # evita que seja alterado manualmente

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
admin.site.register(Estagio, EstagioAdmin) # <-- O mais importante para você agora
admin.site.register(DocumentoEstagio)