from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.db.models import Q, Count
import datetime
from core.decorators import role_required
from core.models import DocumentoEstagio, Estagio, CustomUser

# === DASHBOARD ===

@login_required
@role_required('servidor', 'direcao')
def servidor_dashboard_view(request):
    context = {'user': request.user}
    
    if request.user.tipo == 'direcao':
        documentos_pendentes = DocumentoEstagio.objects.filter(
            status='AGUARDANDO_ASSINATURA_DIR' 
        ).select_related('estagio__aluno', 'estagio__orientador')
        
        context['documentos_pendentes'] = documentos_pendentes
        template_name = 'servidor/direcao/servidor-direcao_dashboard.html'
    
    elif request.user.tipo == 'servidor':
        alunos_no_eixo_count = 0
        if request.user.eixo:
            alunos_no_eixo_count = CustomUser.objects.filter(
                tipo='aluno',
                alunoturma__turma__curso__eixo=request.user.eixo
            ).distinct().count()
        
        context['alunos_no_eixo_count'] = alunos_no_eixo_count
        template_name = 'servidor/administrativo/servidor-administrativo_dashboard.html'
        
    return render(request, template_name, context)


# === SERVIDOR / DIREÇÃO - ESTÁGIO ===

@login_required
@role_required('direcao')
def direcao_assinar_documento(request, documento_id):
    if request.method != 'POST':
        messages.error(request, "Ação inválida.")
        return redirect('servidor_dashboard')

    documento = get_object_or_404(DocumentoEstagio, id=documento_id)
    
    if documento.status != 'AGUARDANDO_ASSINATURA_DIR':
        messages.warning(request, "Este documento não está (ou não está mais) aguardando sua assinatura.")
        return redirect('servidor_dashboard')

    documento.assinado_diretor_em = now()
    documento.assinado_por_diretor = request.user 
    
    documento.status = 'AGUARDANDO_VERIFICACAO_ADMIN'
    documento.save()
    
    messages.success(request, f"Documento '{documento.get_tipo_documento_display()}' assinado e encaminhado para verificação final!")
    return redirect('servidor_dashboard')

@login_required
@role_required('direcao') 
def direcao_visualizar_documento(request, documento_id):
    documento = get_object_or_404(DocumentoEstagio, id=documento_id)
    estagio = documento.estagio
    
    if documento.status not in ['AGUARDANDO_ASSINATURA_DIR', 'CONCLUIDO']:
         messages.error(request, "Este documento não está (ou não está mais) aguardando sua assinatura.")
         return redirect('servidor_dashboard')

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
        return redirect('servidor_dashboard')

    context = {
        'documento': documento,
        'estagio': estagio,
        'aluno': estagio.aluno,
        'dados': dados,
        'pdf_existe': documento.pdf_supervisor_assinado.storage.exists(documento.pdf_supervisor_assinado.name) if documento.pdf_supervisor_assinado else False,
        'pode_assinar_direcao': documento.status == 'AGUARDANDO_ASSINATURA_DIR',
        'documento_ja_assinado_direcao': bool(documento.assinado_diretor_em),
    }
    
    return render(request, template_name, context)


@login_required
@role_required('servidor')
def servidor_monitorar_alunos(request):
    eixo_servidor = request.user.eixo
    if not eixo_servidor:
        messages.error(request, "Seu usuário não está associado a um Eixo.")
        return redirect('servidor_dashboard')

    alunos_no_eixo = CustomUser.objects.filter(
        tipo='aluno',
        alunoturma__turma__curso__eixo=eixo_servidor
    ).distinct().order_by('first_name', 'last_name')

    estagios_map = {
        estagio.aluno_id: estagio
        for estagio in Estagio.objects.filter(
            aluno__in=alunos_no_eixo
        ).annotate(
            docs_pendentes_count=Count('documentos', filter=~Q(documentos__status='CONCLUIDO'))
        )
    }

    alunos_data = []
    for aluno in alunos_no_eixo:
        estagio_data = estagios_map.get(aluno.id)
        alunos_data.append({
            'aluno': aluno,
            'estagio_iniciado': bool(estagio_data),
            'docs_pendentes_count': estagio_data.docs_pendentes_count if estagio_data else 0,
            'estagio_status': estagio_data.get_status_geral_display() if estagio_data else "Não Iniciado",
            'estagio_id': estagio_data.id if estagio_data else None,
        })

    context = {
        'alunos_data': alunos_data,
        'eixo_servidor': request.user.get_eixo_display
    }
    return render(request, 'servidor/administrativo/monitorar_alunos.html', context)


@login_required
@role_required('servidor')
def servidor_ver_documentos_aluno(request, aluno_id):
    eixo_servidor = request.user.eixo
    aluno = get_object_or_404(CustomUser, id=aluno_id, tipo='aluno')

    try:
        estagio = Estagio.objects.get(aluno=aluno)
    except Estagio.DoesNotExist:
        messages.error(request, "Este aluno ainda não iniciou seu dossiê de estágio.")
        return redirect('servidor_monitorar_alunos')

    aluno_pertence_ao_eixo = aluno.alunoturma_set.filter(
        turma__curso__eixo=eixo_servidor
    ).exists()
    
    if not aluno_pertence_ao_eixo:
        messages.error(request, "Você não tem permissão para ver este aluno.")
        return redirect('servidor_monitorar_alunos')

    documentos_qs = estagio.documentos.all()
    ordem_desejada = [
        'TERMO_COMPROMISSO', 'FICHA_IDENTIFICACAO', 'FICHA_PESSOAL',
        'AVALIACAO_ORIENTADOR', 'AVALIACAO_SUPERVISOR', 
        'COMP_RESIDENCIA', 'COMP_AGUA_LUZ', 'ID_CARD', 
        'SUS_CARD', 'VACINA_CARD', 'APOLICE_SEGURO',
    ]
    docs_encontrados = {doc.tipo_documento: doc for doc in documentos_qs}
    documentos_ordenados = []
    for tipo in ordem_desejada:
        if tipo in docs_encontrados:
            documentos_ordenados.append(docs_encontrados[tipo])

    context = {
        'aluno': aluno,
        'estagio': estagio,
        'documentos': documentos_ordenados
    }
    return render(request, 'servidor/administrativo/ver_documentos_aluno.html', context)

@login_required
@role_required('servidor') 
def servidor_visualizar_documento(request, documento_id):
    servidor = request.user
    eixo_servidor = servidor.eixo
    
    documento = get_object_or_404(DocumentoEstagio, id=documento_id)
    estagio = documento.estagio
    aluno = estagio.aluno

    # 1. Validação de Eixo do Servidor
    if not eixo_servidor:
        messages.error(request, "Seu usuário não está associado a um Eixo.")
        return redirect('servidor_monitorar_alunos')

    # 2. Validação de Permissão sobre o Aluno
    aluno_pertence_ao_eixo = aluno.alunoturma_set.filter(
        turma__curso__eixo=eixo_servidor
    ).exists()
    
    if not aluno_pertence_ao_eixo:
        messages.error(request, "Você não tem permissão para ver os documentos deste aluno.")
        return redirect('servidor_monitorar_alunos')
    
    # ==============================================================================
    # === NOVA LÓGICA DE AUTO-CORREÇÃO (SELF-HEALING) ===
    # Verifica a integridade do estágio ao visualizar qualquer documento dele
    # ==============================================================================
    documentos_do_estagio = estagio.documentos.all()
    if documentos_do_estagio.exists():
        pendencias = documentos_do_estagio.exclude(status='CONCLUIDO').exists()
        
        # Se não houver pendências (tudo concluído) e o status ainda não for APROVADO...
        if not pendencias and estagio.status_geral != 'APROVADO':
            estagio.status_geral = 'APROVADO'
            estagio.save()
            # O status atualiza silenciosamente para que, ao carregar a página, 
            # as badges já apareçam corretas.
    # ==============================================================================

    dados = documento.dados_formulario or {}
    
    # Converter datas
    for campo in ['data_inicio', 'data_fim']:
        valor = dados.get(campo)
        if isinstance(valor, str):
            try: dados[campo] = datetime.date.fromisoformat(valor)
            except: pass 
    
    if 'atividades_lista' in dados:
        for item in dados['atividades_lista']:
            data_str = item.get('data')
            if data_str and isinstance(data_str, str):
                try: item['data'] = datetime.date.fromisoformat(data_str)
                except: pass

    # === LÓGICA COMPARTILHADA: DADOS DO TERMO E REAIS ===
    dados_termo = {}
    try:
        termo = DocumentoEstagio.objects.filter(estagio=estagio, tipo_documento='TERMO_COMPROMISSO').first()
        if termo:
            dados_termo = termo.dados_formulario or {}
            for key in ['data_inicio', 'data_fim']:
                 if dados_termo.get(key):
                    try: dados_termo[key] = datetime.date.fromisoformat(dados_termo[key])
                    except: pass
    except: pass

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
    # ====================================================

    template_name = ''

    if documento.tipo_documento == 'TERMO_COMPROMISSO':
        template_name = 'estagio/docs/TERMO-DE-COMPROMISSO/TERMO-DE-COMPROMISSO_VISUALIZAR.html'
        
    elif documento.tipo_documento == 'FICHA_IDENTIFICACAO':
        template_name = 'estagio/docs/FICHA-DE-IDENTIFICACAO/FICHA-DE-IDENTIFICACAO_VISUALIZAR.html'

    elif documento.tipo_documento == 'FICHA_PESSOAL':
        template_name = 'estagio/docs/FICHA-PESSOAL/FICHA-PESSOAL_VISUALIZAR.html'
        
    elif documento.tipo_documento == 'AVALIACAO_ORIENTADOR':
        template_name = 'estagio/docs/AVALIACAO-ORIENTADOR/AVALIACAO-ORIENTADOR_VISUALIZAR.html'
        
    elif documento.tipo_documento == 'AVALIACAO_SUPERVISOR':
        template_name = 'estagio/docs/AVALIACAO-SUPERVISOR/AVALIACAO-SUPERVISOR_VISUALIZAR.html'

    elif documento.tipo_documento in ['COMP_RESIDENCIA', 'COMP_AGUA_LUZ', 'ID_CARD', 'SUS_CARD', 'VACINA_CARD', 'APOLICE_SEGURO']:
        template_name = 'estagio/docs/GENERICO/UPLOAD_SIMPLES.html'

    else:
        messages.info(request, f"A visualização para '{documento.get_tipo_documento_display()}' ainda não foi implementada.")
        return redirect('servidor_ver_documentos_aluno', aluno_id=aluno.id)

    context = {
        'documento': documento,
        'estagio': estagio,
        'aluno': aluno,
        'dados': dados,
        'dados_termo': dados_termo,
        'dados_reais': dados_reais, 
        'pdf_existe': documento.pdf_supervisor_assinado.storage.exists(documento.pdf_supervisor_assinado.name) if documento.pdf_supervisor_assinado else False,
        'user_is_servidor': True,
        'pode_aprovar_servidor': documento.status == 'AGUARDANDO_VERIFICACAO_ADMIN',
        'pode_reprovar_servidor': documento.status == 'AGUARDANDO_VERIFICACAO_ADMIN',
    }
    
    return render(request, template_name, context)


@login_required
@role_required('servidor')
def servidor_reprovar_documento(request, documento_id):
    if request.method != 'POST':
        return redirect('servidor_monitorar_alunos') 

    documento = get_object_or_404(DocumentoEstagio, id=documento_id)
    estagio = documento.estagio
    aluno = estagio.aluno
    servidor = request.user
    aluno_pertence_ao_eixo = aluno.alunoturma_set.filter(
        turma__curso__eixo=servidor.eixo
    ).exists()
    
    if not aluno_pertence_ao_eixo:
        messages.error(request, "Você não tem permissão para gerenciar este documento.")
        return redirect('servidor_monitorar_alunos')

    documento.assinado_aluno_em = None
    documento.assinado_orientador_em = None
    documento.assinado_diretor_em = None
    
    if documento.pdf_supervisor_assinado:
        documento.pdf_supervisor_assinado.delete(save=False)
    
    documento.status = 'REPROVADO'
    documento.save()
    
    estagio.status_geral = 'PENDENTE_CORRECAO'
    estagio.save()
    
    messages.warning(request, f"O documento '{documento.get_tipo_documento_display()}' foi reprovado e devolvido ao aluno para correção.")
    return redirect('servidor_ver_documentos_aluno', aluno_id=aluno.id)


@login_required
@role_required('servidor')
def servidor_aprovar_documento(request, documento_id):
    # 1. Verificações Iniciais (Método POST)
    if request.method != 'POST':
        return redirect('servidor_monitorar_alunos')

    documento = get_object_or_404(DocumentoEstagio, id=documento_id)
    estagio = documento.estagio
    aluno = estagio.aluno
    servidor = request.user
    
    # 2. Verificação de Segurança (Eixo)
    aluno_pertence_ao_eixo = aluno.alunoturma_set.filter(
        turma__curso__eixo=servidor.eixo
    ).exists()
    
    if not aluno_pertence_ao_eixo:
        messages.error(request, "Você não tem permissão para gerenciar este documento.")
        return redirect('servidor_monitorar_alunos')

    # 3. Evitar retrabalho
    if documento.status == 'CONCLUIDO':
        messages.info(request, "Este documento já estava aprovado.")
        return redirect('servidor_ver_documentos_aluno', aluno_id=aluno.id)

    # 4. APROVAÇÃO DO DOCUMENTO INDIVIDUAL
    documento.status = 'CONCLUIDO'
    documento.save()
    
    # ==============================================================================
    # NOVA LÓGICA: VERIFICAÇÃO DE CONCLUSÃO DO DOSSIÊ
    # ==============================================================================
    
    # Pergunta ao banco: "Existe algum documento deste estágio que NÃO seja 'CONCLUIDO'?"
    pendencias = DocumentoEstagio.objects.filter(estagio=estagio).exclude(status='CONCLUIDO').exists()
    
    if not pendencias:
        # Se NÃO há pendências (a lista de 'não concluídos' está vazia),
        # significa que tudo está pronto. Aprovamos o estágio geral!
        estagio.status_geral = 'APROVADO'
        estagio.save()
        
        messages.success(
            request, 
            f"O documento '{documento.get_tipo_documento_display()}' foi aprovado e o Dossiê de Estágio foi FINALIZADO com sucesso!"
        )
    else:
        # Se ainda houver documentos pendentes, apenas avisa que este foi aprovado
        # Opcional: Garante que o status geral reflita que está andando
        if estagio.status_geral in ['RASCUNHO_ALUNO', 'PENDENTE_CORRECAO']:
             estagio.status_geral = 'EM_ANDAMENTO'
             estagio.save()

        messages.success(request, f"O documento '{documento.get_tipo_documento_display()}' foi APROVADO com sucesso!")
        
    # ==============================================================================

    return redirect('servidor_ver_documentos_aluno', aluno_id=aluno.id)