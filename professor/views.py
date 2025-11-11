from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
import datetime
from core.decorators import role_required
from core.models import (
    ProfessorMateriaAnoCursoModalidade,
    DocumentoEstagio,
    Materia,
    Turma,
    CustomUser,
    Nota
)

# === DASHBOARD ===

@login_required
@role_required('professor')
def professor_dashboard_view(request):
    vinculos = ProfessorMateriaAnoCursoModalidade.objects.filter(
        professor=request.user
    ).select_related('materia', 'curso')

    documentos_pendentes = DocumentoEstagio.objects.filter(
        estagio__orientador=request.user,
        status='AGUARDANDO_ASSINATURA_PROF' 
    ).select_related('estagio__aluno')

    context = {
        'vinculos': vinculos,
        'documentos_pendentes': documentos_pendentes 
    }
    return render(request, 'professor/professor_dashboard.html', context)


# === MATÉRIAS-ANO-CURSO-MODALIDADE-ESTÁGIO ===

@login_required
@role_required('professor')
def listar_turmas_vinculadas(request, vinculo_id):
    vinculo = get_object_or_404(ProfessorMateriaAnoCursoModalidade, id=vinculo_id, professor=request.user)

    turmas = Turma.objects.filter(
        curso=vinculo.curso,
        ano_modulo=vinculo.ano_modulo,
        modalidade=vinculo.modalidade
    )

    context = {
        'vinculo': vinculo,
        'turmas': turmas
    }
    return render(request, 'professor/lescionação/listar_turmas_vinculadas.html', context)

@login_required
@role_required('professor')
def detalhar_turma_professor(request, materia_id, turma_id):
    materia = get_object_or_404(Materia, id=materia_id)
    turma = get_object_or_404(Turma, id=turma_id)

    vinculado = ProfessorMateriaAnoCursoModalidade.objects.filter(
        professor=request.user,
        materia=materia,
        curso=turma.curso,
        ano_modulo=turma.ano_modulo,
        modalidade=turma.modalidade
    ).exists()

    if not vinculado:
        messages.error(request, "Você não tem permissão para lecionar esta matéria nesta turma.")
        return redirect('professor_dashboard')

    alunos = CustomUser.objects.filter(tipo='aluno', alunoturma__turma=turma).distinct()
    notas_dict = {nota.aluno.id: nota for nota in Nota.objects.filter(materia=materia, turma=turma)}
    
    context = {
        'materia': materia, 'turma': turma, 'alunos': alunos, 'notas_dict': notas_dict
    }
    return render(request, 'professor/lescionação/detalhar_turma.html', context)
    
@login_required
@role_required('professor')
def ver_turma_professor(request, materia_id, turma_id):
    materia = get_object_or_404(Materia, id=materia_id)
    turma = get_object_or_404(Turma, id=turma_id)

    if not ProfessorMateriaAnoCursoModalidade.objects.filter(professor=request.user, materia=materia, turma=turma).exists():
        messages.error(request, "Você não tem acesso a essa turma.")
        return redirect('professor_dashboard')

    alunos = CustomUser.objects.filter(tipo='aluno', alunoturma__turma=turma).distinct()
    notas_dict = {nota.aluno_id: nota for nota in Nota.objects.filter(materia=materia, turma=turma)}

    return render(request, 'professor/lescionação/detalhar_turma.html', {
        'materia': materia,
        'turma': turma,
        'alunos': alunos,
        'notas_dict': notas_dict
    })

@login_required
@role_required('professor')
def ver_detalhes_aluno_professor(request, aluno_id):
    aluno = get_object_or_404(CustomUser, id=aluno_id, tipo='aluno')
    turmas = Turma.objects.filter(alunoturma__aluno=aluno)
    return render(request, 'professor/lescionação/detalhes_aluno.html', {'aluno': aluno, 'turmas': turmas})


@login_required
@role_required('professor')
def professor_assinar_documento(request, documento_id):
    if request.method != 'POST':
        messages.error(request, "Ação inválida.")
        return redirect('professor_dashboard')

    documento = get_object_or_404(DocumentoEstagio, id=documento_id)
    estagio = documento.estagio

    if estagio.orientador != request.user:
        messages.error(request, "Você não tem permissão para assinar este documento.")
        return redirect('professor_dashboard')
    
    if documento.status != 'AGUARDANDO_ASSINATURA_PROF':
        messages.warning(request, "Este documento não está (ou não está mais) aguardando sua assinatura.")
        return redirect('professor_dashboard')

    documento.assinado_orientador_em = now()
    documento.assinado_por_orientador = request.user 
    
    tipo = documento.tipo_documento
    
    if tipo == 'TERMO_COMPROMISSO':
        documento.status = 'AGUARDANDO_ASSINATURA_DIR'
    elif tipo == 'FICHA_PESSOAL' or tipo == 'AVALIACAO_ORIENTADOR':
        documento.status = 'AGUARDANDO_VERIFICACAO_ADMIN'
    else:
        documento.status = 'AGUARDANDO_VERIFICACAO_ADMIN'
        
    documento.save()
    
    messages.success(request, f"Documento '{documento.get_tipo_documento_display()}' assinado e encaminhado!")
    return redirect('professor_dashboard')


@login_required
@role_required('professor')
def professor_visualizar_documento(request, documento_id):
    documento = get_object_or_404(DocumentoEstagio, id=documento_id)
    estagio = documento.estagio

    if estagio.orientador != request.user:
        messages.error(request, "Você não tem permissão para visualizar este documento.")
        return redirect('professor_dashboard')

    dados = documento.dados_formulario or {}
    for campo in ['data_inicio', 'data_fim']:
        valor = dados.get(campo)
        if isinstance(valor, str):
            try:
                dados[campo] = datetime.date.fromisoformat(valor)
            except ValueError:
                pass 
    
    if documento.tipo_documento == 'TERMO_COMPROMISSO':
        template_name = 'estagio/docs/TERMO-DE-COMPROMISSO/TERMO-DE-COMPROMISSO_VISUALIZAR.html'
    else:
        messages.info(request, f"A visualização para '{documento.get_tipo_documento_display()}' ainda não foi implementada.")
        return redirect('professor_dashboard')

    context = {
        'documento': documento,
        'estagio': estagio,
        'aluno': estagio.aluno,
        'dados': dados,
        'pdf_existe': documento.pdf_supervisor_assinado.storage.exists(documento.pdf_supervisor_assinado.name) if documento.pdf_supervisor_assinado else False,
        'pode_assinar_orientador': documento.status == 'AGUARDANDO_ASSINATURA_PROF',
        'documento_ja_assinado_orientador': bool(documento.assinado_orientador_em),
    }
    
    return render(request, template_name, context)