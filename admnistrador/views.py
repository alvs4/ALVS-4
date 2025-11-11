from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from core.decorators import role_required
from core.models import CustomUser, ProfessorMateriaAnoCursoModalidade, Curso, Turma, Materia
from autenticacao.forms import (
    ProfessorCreateForm,
    ProfessorMateriaAnoCursoModalidadeFormSet,
    AlunoCreateForm,
    ServidorCreateForm,
)

# === DASHBOARD ===

@login_required
@role_required('admin')
def admin_dashboard_view(request):
    return render(request, 'admin/admin_dashboard.html')

# === CRUD - PROFESSORES ===

@login_required
@role_required('admin')
def gerenciar_professores(request):
    professores = CustomUser.objects.filter(tipo='professor').order_by('first_name', 'last_name') 
    return render(request, 'admin/professor_crud/gerenciar_professores.html', {'professores': professores})


@login_required
@role_required('admin')
def ver_detalhes_professor(request, professor_id):
    professor = get_object_or_404(CustomUser, id=professor_id, tipo='professor')
    vinculos = ProfessorMateriaAnoCursoModalidade.objects.filter(professor=professor).select_related('materia', 'curso')

    return render(request, 'admin/professor_crud/detalhes_professor.html', {
        'professor': professor,
        'vinculos': vinculos,
    })


@login_required
@role_required('admin')
def cadastrar_professor(request):
    if request.method == 'POST':
        form = ProfessorCreateForm(request.POST)
        formset = ProfessorMateriaAnoCursoModalidadeFormSet(request.POST, queryset=ProfessorMateriaAnoCursoModalidade.objects.none())

        if form.is_valid() and formset.is_valid():
            professor = form.save() 

            instances = formset.save(commit=False)
            for instance in instances:
                instance.professor = professor
                instance.save()
            
            messages.success(request, "Professor cadastrado com sucesso.")
            return redirect('gerenciar_professores')
        else:
            messages.error(request, "Erro ao cadastrar. Verifique os campos do professor e dos vínculos.")
    else:
        form = ProfessorCreateForm()
        formset = ProfessorMateriaAnoCursoModalidadeFormSet(queryset=ProfessorMateriaAnoCursoModalidade.objects.none())

    return render(request, 'admin/professor_crud/cadastrar_professor.html', {
        'form': form,
        'formset': formset
    })


@login_required
@role_required('admin')
def editar_professor(request, professor_id):
    professor = get_object_or_404(CustomUser, id=professor_id, tipo='professor')
    
    form = ProfessorCreateForm(request.POST or None, instance=professor)
    formset = ProfessorMateriaAnoCursoModalidadeFormSet(
        request.POST or None,
        queryset=ProfessorMateriaAnoCursoModalidade.objects.filter(professor=professor)
    )

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        form.save()
        
        instances = formset.save(commit=False)
        for instance in instances:
            instance.professor = professor
            instance.save()
        
        for obj in formset.deleted_objects:
            obj.delete()

        messages.success(request, "Professor atualizado com sucesso.")
        return redirect('gerenciar_professores')

    return render(request, 'admin/professor_crud/editar_professor.html', {
        'form': form,
        'formset': formset,
        'professor': professor
    })


@login_required
@role_required('admin')
def remover_professor(request, professor_id):
    professor = get_object_or_404(CustomUser, id=professor_id, tipo='professor')

    if request.method == 'POST':
        professor.delete()
        messages.success(request, "Professor removido com sucesso.")
        return redirect('gerenciar_professores')

    return render(request, 'admin/professor_crud/remover_professor.html', {'professor': professor})


# === CRUD - ALUNOS ===

@login_required
@role_required('admin')
def gerenciar_alunos(request):
    alunos = CustomUser.objects.filter(tipo='aluno').prefetch_related('alunoturma_set__turma').order_by('first_name', 'last_name')
    return render(request, 'admin/aluno_crud/gerenciar_alunos.html', {'alunos': alunos})


@login_required
@role_required('admin')
def cadastrar_aluno(request):
    if request.method == 'POST':
        print("="*30)
        print("🧾 DADOS RECEBIDOS DO FORMULÁRIO (NO BACKEND):")
        print(f"Curso ID: {request.POST.get('curso')}")
        print(f"Ano/Módulo: {request.POST.get('ano_modulo')}")
        print(f"Turno: {request.POST.get('turno')}")
        print(f"Turma ID: {request.POST.get('turma')}")
        print("="*30)

        form = AlunoCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Aluno cadastrado com sucesso.")
            return redirect('gerenciar_alunos')
        else:
            print("\n⚠️ ERROS DE VALIDAÇÃO DO FORMULÁRIO:")
            print(form.errors.as_json())
            print("-" * 30 + "\n")
            messages.error(request, "Erro ao salvar. Verifique os campos.")
    else:
        form = AlunoCreateForm()
        
    return render(request, 'admin/aluno_crud/cadastrar_aluno.html', {'form': form})


@login_required
@role_required('admin')
def editar_aluno(request, aluno_id):
    aluno = get_object_or_404(CustomUser, id=aluno_id, tipo='aluno')

    if request.method == 'POST':
        curso_id = request.POST.get('curso')
        ano_modulo = request.POST.get('ano_modulo')
        turno = request.POST.get('turno')

        print("="*40)
        print("🧾 DADOS RECEBIDOS NO POST (Editar Aluno):")
        print(f"Curso ID: {curso_id}")
        print(f"Ano/Módulo: {ano_modulo}")
        print(f"Turno: {turno}")
        print(f"Turma ID: {request.POST.get('turma')}")
        print("="*40)

        form = AlunoCreateForm(request.POST, instance=aluno)

        turmas_queryset = Turma.objects.all()
        if curso_id:
            turmas_queryset = turmas_queryset.filter(curso_id=curso_id)
        if ano_modulo:
            turmas_queryset = turmas_queryset.filter(ano_modulo=ano_modulo)
        if turno:
            turmas_queryset = turmas_queryset.filter(turno=turno)

        form.fields['turma'].queryset = turmas_queryset
        form.fields['turno'].choices = [
            (valor, label) for valor, label in Turma.TURNO_CHOICES
            if valor in turmas_queryset.values_list('turno', flat=True)
        ]

        if form.is_valid():
            form.save()
            messages.success(request, "Aluno atualizado com sucesso.")
            return redirect('gerenciar_alunos')
        else:
            print("\n⚠️ ERROS DE VALIDAÇÃO:")
            print(form.errors.as_json())
            print("-" * 40)
            messages.error(request, "Erro ao salvar. Verifique os campos.")
    else:
        form = AlunoCreateForm(instance=aluno)

        if hasattr(aluno, 'alunoturma_set') and aluno.alunoturma_set.exists():
            turma_atual = aluno.alunoturma_set.first().turma
            turmas_queryset = Turma.objects.filter(
                curso=turma_atual.curso,
                ano_modulo=turma_atual.ano_modulo,
                turno=turma_atual.turno
            )
            form.fields['turma'].queryset = turmas_queryset
            form.fields['turno'].choices = [
                (turma_atual.turno, turma_atual.get_turno_display())
            ]

    context = {
        'form': form,
        'aluno': aluno
    }
    return render(request, 'admin/aluno_crud/editar_aluno.html', context)


@login_required
@role_required('admin')
def remover_aluno(request, aluno_id):
    aluno = get_object_or_404(CustomUser, id=aluno_id, tipo='aluno')

    if request.method == 'POST':
        aluno.delete()
        messages.success(request, "Aluno removido com sucesso.")
        return redirect('gerenciar_alunos')

    return render(request, 'admin/aluno_crud/remover_aluno.html', {'aluno': aluno})


@login_required
@role_required('admin')
def ver_detalhes_aluno(request, aluno_id):
    aluno = get_object_or_404(CustomUser, id=aluno_id, tipo='aluno')
    turmas = aluno.alunoturma_set.all()
    return render(request, 'admin/aluno_crud/detalhes_aluno.html', {'aluno': aluno, 'turmas': turmas})

# === CRUD - SERVIDORES ===

@login_required
@role_required('admin')
def gerenciar_servidores(request):
    servidores = CustomUser.objects.filter(
        tipo__in=['servidor', 'direcao']
    ).order_by('first_name', 'last_name')
    
    return render(request, 'admin/servidor_crud/gerenciar_servidores.html', {'servidores': servidores})

@login_required
@role_required('admin')
def cadastrar_servidor(request):
    if request.method == 'POST':
        form = ServidorCreateForm(request.POST)
        if form.is_valid():
            servidor = form.save(commit=False)
            tipo_escolhido = form.cleaned_data['tipo_usuario']
            servidor.tipo = tipo_escolhido 
            servidor.save() 
            messages.success(request, "Servidor cadastrado com sucesso.")
            return redirect('gerenciar_servidores')
        else:
            messages.error(request, "Erro ao cadastrar o servidor. Verifique os campos.")
    else:
        form = ServidorCreateForm()
    return render(request, 'admin/servidor_crud/cadastrar_servidor.html', {'form': form})

@login_required
@role_required('admin')
def editar_servidor(request, servidor_id):
    servidor = get_object_or_404(CustomUser, id=servidor_id, tipo__in=['servidor', 'direcao'])

    if request.method == 'POST':
        form = ServidorCreateForm(request.POST, instance=servidor)
        if form.is_valid():
            tipo_usuario = form.cleaned_data['tipo_usuario']
            eixo = form.cleaned_data.get('eixo')

            user = form.save(commit=False)
            
            user.tipo = tipo_usuario
            if tipo_usuario == 'servidor':
                user.eixo = eixo
            else:  
                user.eixo = None
            
            user.save()

            messages.success(request, "Dados atualizados com sucesso.")
            return redirect('gerenciar_servidores')
    else:
        initial_data = {'tipo_usuario': servidor.tipo}
        form = ServidorCreateForm(instance=servidor, initial=initial_data)

    context = {
        'form': form,
        'servidor': servidor,
    }
    return render(request, 'admin/servidor_crud/editar_servidor.html', context)

@login_required
@role_required('admin')
def remover_servidor(request, servidor_id):
    servidor = get_object_or_404(
        CustomUser, 
        id=servidor_id, 
        tipo__in=['servidor', 'direcao']
    )
    
    if request.method == 'POST':
        servidor.delete()
        messages.success(request, "Servidor removido com sucesso.")
        return redirect('gerenciar_servidores')
    
    return render(request, 'admin/servidor_crud/remover_servidor.html', {'servidor': servidor})


@login_required
@role_required('admin')
def ver_detalhes_servidor(request, servidor_id):
    servidor = get_object_or_404(
        CustomUser, 
        id=servidor_id, 
        tipo__in=['servidor', 'direcao']
    )
    
    context = {
        'servidor': servidor
    }
    return render(request, 'admin/servidor_crud/detalhes_servidor.html', context)

# === CRUD - TURMAS ===

@login_required
@role_required('admin') 
def listar_turmas(request):
    cursos = Curso.objects.all().order_by('nome') 
    
    return render(request, 'admin/turmas_crud/listar_turmas.html', {
        'cursos': cursos 
    })


@login_required
@role_required('admin') 
def listar_turmas_por_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    turmas = Turma.objects.filter(curso=curso).order_by('ano_modulo', 'turno', 'turma')
    
    return render(request, 'admin/turmas_crud/listar_turmas_por_curso.html', {
        'curso': curso,
        'turmas': turmas
    })


@login_required
@role_required('admin')
def detalhar_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    alunos = CustomUser.objects.filter(alunoturma__turma=turma, tipo='aluno')
    return render(request, 'admin/turmas_crud/detalhar_turma.html', {'turma': turma, 'alunos': alunos})

# === CRUD - MATÉRIAS ===

@login_required
@role_required('admin')
def listar_materias(request):
    cursos = Curso.objects.all().order_by('nome') 
    return render(request, 'admin/materias_crud/listar_materias.html', {
        'cursos': cursos 
    })


@login_required
@role_required('admin')
def listar_materias_por_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    materias_tecnicas = curso.materias.filter(
        em_grades__curso=curso, 
        em_grades__tipo='TECNICA'
    ).order_by('nome')
    
    materias_base = curso.materias.filter(
        em_grades__curso=curso, 
        em_grades__tipo='BASE'
    ).order_by('nome')
    
    return render(request, 'admin/materias_crud/listar_materias_por_curso.html', {
        'curso': curso,
        'materias_tecnicas': materias_tecnicas,
        'materias_base': materias_base
    })


@login_required
@role_required('admin')
def detalhar_materia(request, materia_id):
    materia = get_object_or_404(Materia, id=materia_id)
    
    vinculos = ProfessorMateriaAnoCursoModalidade.objects.filter(
        materia=materia
    ).select_related('professor', 'curso')

    professores_com_vinculos = defaultdict(list)
    
    for v in vinculos:
        descricao_vinculo = f"{v.ano_modulo} ({v.modalidade})"
        professores_com_vinculos[v.professor].append(descricao_vinculo)

    context_data = [(prof, vinculos) for prof, vinculos in professores_com_vinculos.items()]
    
    return render(request, 'admin/materias_crud/detalhar_materia.html', {
        'materia': materia,
        'professores_com_vinculos': context_data
    })