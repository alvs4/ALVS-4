from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.db.models import Q
import datetime
from core.decorators import role_required
from autenticacao.forms import AvaliacaoOrientadorForm
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

    # 1. Documentos que realmente precisam da ação do professor
    documentos_prof = DocumentoEstagio.objects.filter(
        estagio__orientador=request.user
    ).exclude(
        tipo_documento='AVALIACAO_SUPERVISOR'
    ).filter(
        Q(status='AGUARDANDO_ASSINATURA_PROF')
    )

    # 2. Agora aplicamos a lógica para EXIBIR a Avaliação do Orientador
    avaliacoes = []
    avaliacoes_queryset = DocumentoEstagio.objects.filter(
        estagio__orientador=request.user,
        tipo_documento='AVALIACAO_ORIENTADOR',
        status__in=['RASCUNHO', 'RASCUNHO_ORIENTADOR', 'AGUARDANDO_ASSINATURA_PROF']
    )

    for doc in avaliacoes_queryset:
        estagio = doc.estagio

        # buscar todos os outros documentos do estágio
        outros_docs = DocumentoEstagio.objects.filter(
            estagio=estagio
        ).exclude(
            tipo_documento__in=['AVALIACAO_ORIENTADOR', 'AVALIACAO_SUPERVISOR']
        )

        # verificar se todos eles estão finalizados / completos
        tudo_ok = all(d.status == 'CONCLUIDO' for d in outros_docs)

        if tudo_ok:
            avaliacoes.append(doc)

    # juntar tudo no mesmo queryset-like (lista)
    documentos_pendentes = list(documentos_prof) + list(avaliacoes)

    # ordenar pelo nome do aluno
    documentos_pendentes.sort(key=lambda x: x.estagio.aluno.first_name)

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

    # Segurança: apenas o orientador pode assinar
    if estagio.orientador != request.user:
        messages.error(request, "Você não tem permissão para assinar este documento.")
        return redirect('professor_dashboard')

    tipo = documento.tipo_documento

    # ---------------------------------------------------
    # ⭐ FLUXO EXCLUSIVO PARA AVALIAÇÃO DO ORIENTADOR ⭐
    # ---------------------------------------------------
    if tipo == 'AVALIACAO_ORIENTADOR':
        # A avaliação pode ser assinada mesmo em RASCUNHO
        if documento.status not in ['RASCUNHO', 'RASCUNHO_ORIENTADOR', 'AGUARDANDO_ASSINATURA_PROF']:
            messages.error(request, "Esta avaliação não está pronta para assinatura.")
            return redirect('professor_dashboard')

        documento.assinado_orientador_em = now()
        documento.assinado_por_orientador = request.user
        documento.status = 'CONCLUIDO'
        documento.save()

        messages.success(request, "Avaliação do orientador assinada e concluída com sucesso!")
        return redirect('professor_dashboard')

    # ---------------------------------------------------
    # FLUXO NORMAL PARA OUTROS DOCUMENTOS
    # ---------------------------------------------------
    if documento.status != 'AGUARDANDO_ASSINATURA_PROF':
        messages.warning(request, "Este documento não está (ou não está mais) aguardando sua assinatura.")
        return redirect('professor_dashboard')

    documento.assinado_orientador_em = now()
    documento.assinado_por_orientador = request.user 

    if tipo == 'TERMO_COMPROMISSO':
        documento.status = 'AGUARDANDO_ASSINATURA_DIR'

    elif tipo == 'FICHA_PESSOAL':
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
    
    # 1. Converter datas do cabeçalho
    for campo in ['data_inicio', 'data_fim']:
        valor = dados.get(campo)
        if isinstance(valor, str):
            try: dados[campo] = datetime.date.fromisoformat(valor)
            except: pass 
    
    # 2. Converter datas da tabela de atividades (para Ficha Pessoal)
    if 'atividades_lista' in dados:
        for item in dados['atividades_lista']:
            data_str = item.get('data')
            if data_str and isinstance(data_str, str):
                try: item['data'] = datetime.date.fromisoformat(data_str)
                except: pass

    # === LÓGICA COMPARTILHADA: DADOS DO TERMO E DADOS REAIS ===
    # Necessário para preencher cabeçalhos da Ficha Pessoal e Avaliação
    dados_termo = {}
    try:
        termo = DocumentoEstagio.objects.filter(estagio=estagio, tipo_documento='TERMO_COMPROMISSO').first()
        if termo:
            dados_termo = termo.dados_formulario or {}
            # Converte datas do termo também
            for key in ['data_inicio', 'data_fim']:
                 if dados_termo.get(key):
                    try: dados_termo[key] = datetime.date.fromisoformat(dados_termo[key])
                    except: pass
    except: pass

    # Busca Dados Reais da Ficha Pessoal (Para o cabeçalho da Avaliação)
    dados_reais = {}
    try:
        ficha = DocumentoEstagio.objects.filter(estagio=estagio, tipo_documento='FICHA_PESSOAL').first()
        if ficha:
            dados_ficha = ficha.dados_formulario or {}
            if dados_ficha.get('total_horas'):
                dados_reais['total_horas'] = dados_ficha.get('total_horas')
            
            atividades = dados_ficha.get('atividades_lista', [])
            datas_validas = []
            for item in atividades:
                if item.get('data'):
                    try: datas_validas.append(datetime.date.fromisoformat(item.get('data')))
                    except: pass
            if datas_validas:
                datas_validas.sort()
                dados_reais['data_inicio'] = datas_validas[0]
                dados_reais['data_fim'] = datas_validas[-1]
    except: pass
    # ==========================================================

    template_name = ''

    if documento.tipo_documento == 'TERMO_COMPROMISSO':
        template_name = 'estagio/docs/TERMO-DE-COMPROMISSO/TERMO-DE-COMPROMISSO_VISUALIZAR.html'
    
    elif documento.tipo_documento == 'FICHA_PESSOAL':
        template_name = 'estagio/docs/FICHA-PESSOAL/FICHA-PESSOAL_VISUALIZAR.html'

    elif documento.tipo_documento == 'AVALIACAO_ORIENTADOR':
        template_name = 'estagio/docs/AVALIACAO-ORIENTADOR/AVALIACAO-ORIENTADOR_VISUALIZAR.html'
        
    else:
        messages.info(request, f"A visualização para '{documento.get_tipo_documento_display()}' ainda não foi implementada.")
        return redirect('professor_dashboard')

    # Permissão para Assinar
    pode_assinar = False
    if documento.status == 'AGUARDANDO_ASSINATURA_PROF':
        pode_assinar = True
    elif documento.tipo_documento == 'AVALIACAO_ORIENTADOR' and documento.status in ['RASCUNHO', 'RASCUNHO_ORIENTADOR']:
        pode_assinar = True

    context = {
        'documento': documento,
        'estagio': estagio,
        'aluno': estagio.aluno,
        'dados': dados,
        'dados_termo': dados_termo, 
        'dados_reais': dados_reais, # IMPORTANTE PARA AVALIAÇÃO
        'pdf_existe': documento.pdf_supervisor_assinado.storage.exists(documento.pdf_supervisor_assinado.name) if documento.pdf_supervisor_assinado else False,
        'pode_assinar_orientador': pode_assinar,
        'documento_ja_assinado_orientador': bool(documento.assinado_orientador_em),
    }
    
    return render(request, template_name, context)


@login_required
@role_required('professor')
def professor_preencher_documento(request, documento_id):
    documento = get_object_or_404(DocumentoEstagio, id=documento_id)
    estagio = documento.estagio

    # Validação: Só o orientador pode preencher
    if estagio.orientador != request.user:
        messages.error(request, "Apenas o orientador deste estágio pode preencher esta avaliação.")
        return redirect('professor_dashboard')

    if documento.tipo_documento != 'AVALIACAO_ORIENTADOR':
        messages.error(request, "Documento inválido para preenchimento do professor.")
        return redirect('professor_dashboard')

    # === LÓGICA INTELIGENTE: BUSCAR DADOS REAIS DA FICHA PESSOAL ===
    # O objetivo é obter o período REAL (datas das atividades) e o Total de Horas calculado pelo aluno.
    dados_reais = {}
    ficha_pessoal_id = None
    
    try:
        ficha = DocumentoEstagio.objects.filter(estagio=estagio, tipo_documento='FICHA_PESSOAL').first()
        if ficha:
            ficha_pessoal_id = ficha.id # Para criar o botão de "Ver Ficha"
            dados_ficha = ficha.dados_formulario or {}
            
            # 1. Captura o Total de Horas que o aluno somou
            if dados_ficha.get('total_horas'):
                dados_reais['total_horas'] = dados_ficha.get('total_horas')

            # 2. Calcula o Período Real baseado nas datas das atividades
            atividades = dados_ficha.get('atividades_lista', [])
            datas_validas = []
            
            for item in atividades:
                data_str = item.get('data')
                if data_str:
                    try:
                        # Converte string para objeto date para poder ordenar corretamente
                        data_obj = datetime.date.fromisoformat(data_str)
                        datas_validas.append(data_obj)
                    except ValueError:
                        pass
            
            if datas_validas:
                datas_validas.sort() # Ordena da mais antiga para a mais recente
                dados_reais['data_inicio'] = datas_validas[0] # A primeira atividade
                dados_reais['data_fim'] = datas_validas[-1]   # A última atividade
                
    except Exception as e:
        # Em caso de erro na leitura (ex: json corrompido), segue sem dados reais
        pass
    # ===============================================================

    if request.method == 'POST':
        form = AvaliacaoOrientadorForm(request.POST)
        if form.is_valid():
            documento.dados_formulario = form.cleaned_data
            documento.save()
            messages.success(request, "Avaliação salva com sucesso!")
            
            # Se clicar em "Salvar e Assinar"
            if 'assinar_agora' in request.POST:
                 return redirect('professor_assinar_documento', documento_id=documento.id)
                 
            return redirect('professor_visualizar_documento', documento_id=documento.id)
    else:
        # Prepara os dados iniciais do formulário
        initial_data = documento.dados_formulario or {}
        
        # Se o professor ainda não preencheu o total de horas na avaliação,
        # sugerimos automaticamente o valor que veio da Ficha Pessoal
        if not initial_data.get('total_horas') and dados_reais.get('total_horas'):
            initial_data['total_horas'] = dados_reais.get('total_horas')
            
        form = AvaliacaoOrientadorForm(initial=initial_data)

    # === DADOS DO TERMO (EXPECTATIVA) ===
    # Serve como "Plano B" caso a ficha pessoal esteja vazia ou incompleta
    dados_termo = {}
    try:
        termo = DocumentoEstagio.objects.filter(estagio=estagio, tipo_documento='TERMO_COMPROMISSO').first()
        if termo: 
            dados_termo = termo.dados_formulario or {}
            
            # Converte datas do termo para objetos date (para formatação bonita no template)
            for key in ['data_inicio', 'data_fim']:
                 if dados_termo.get(key):
                    try: dados_termo[key] = datetime.date.fromisoformat(dados_termo[key])
                    except: pass
    except: 
        pass
    
    context = {
        'form': form,
        'documento': documento,
        'estagio': estagio,
        'aluno': estagio.aluno,
        'dados_termo': dados_termo,   # Dados Planejados (Contrato)
        'dados_reais': dados_reais,   # Dados Executados (Ficha Pessoal)
        'ficha_pessoal_id': ficha_pessoal_id, # ID para linkar o botão
    }
    return render(request, 'estagio/docs/AVALIACAO-ORIENTADOR/AVALIACAO-ORIENTADOR_EDITAR.html', context)