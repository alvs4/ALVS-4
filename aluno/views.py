from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
import datetime
from core.decorators import role_required
from core.models import Nota, Estagio, DocumentoEstagio
from autenticacao.forms import TermoCompromissoForm, FichaIdentificacaoForm

# === DASHBOARD ===

@login_required
@role_required('aluno')
def aluno_dashboard_view(request):
    aluno = request.user
    notas = Nota.objects.filter(aluno=aluno).select_related('materia', 'turma')

    return render(request, 'aluno/aluno_dashboard.html', {
        'notas': notas,
        'aluno': aluno
    })


# === ESTÁGIO ===


@login_required
@role_required('aluno')
def gestao_estagio_aluno(request):
    hoje = datetime.date.today()
    estagio, criado = Estagio.objects.get_or_create(
        aluno=request.user,
        defaults={
            'status_geral': 'RASCUNHO_ALUNO',
            'data_inicio': hoje,
            'data_fim': hoje,
            'supervisor_nome': '(Ainda não definido)', 
            'supervisor_empresa': '(Ainda não definido)',
            'supervisor_cargo': '(Ainda não definido)',
        }
    )

    if criado:
        tipos_de_documento = DocumentoEstagio.TIPO_DOCUMENTO_CHOICES
        documentos_para_criar = []
        for tipo_id, nome_legivel in tipos_de_documento:
            documentos_para_criar.append(
                DocumentoEstagio(
                    estagio=estagio,
                    tipo_documento=tipo_id,
                    status='RASCUNHO' 
                )
            )
        DocumentoEstagio.objects.bulk_create(documentos_para_criar)
        messages.info(request, "Seu Dossiê de Estágio foi criado. Por favor, preencha os documentos necessários.")

    return redirect('detalhes_estagio_aluno')


@login_required
@role_required('aluno')
def detalhes_estagio_aluno(request):
    estagio = get_object_or_404(Estagio, aluno=request.user)
    documentos_qs = DocumentoEstagio.objects.filter(estagio=estagio)
    
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
        'estagio': estagio,
        'documentos': documentos_ordenados,
    }

    return render(request, 'aluno/estagio/detalhes_estagio.html', context)


@login_required
@role_required('aluno')
def visualizar_documento_estagio(request, documento_id):
    documento = get_object_or_404(DocumentoEstagio, id=documento_id, estagio__aluno=request.user)
    estagio = documento.estagio 

    if documento.tipo_documento == 'TERMO_COMPROMISSO':
        template_name = 'estagio/docs/TERMO-DE-COMPROMISSO/TERMO-DE-COMPROMISSO_VISUALIZAR.html'
        
    elif documento.tipo_documento == 'FICHA_IDENTIFICACAO':
        template_name = 'estagio/docs/FICHA-DE-IDENTIFICACAO/FICHA-DE-IDENTIFICACAO_VISUALIZAR.html'
        
    else:
        messages.error(request, "A visualização para este tipo de documento ainda não foi criada.")
        return redirect('detalhes_estagio_aluno')

    dados = documento.dados_formulario or {}

    for campo in ['data_inicio', 'data_fim']:
        valor = dados.get(campo)
        if isinstance(valor, str):
            try:
                dados[campo] = datetime.date.fromisoformat(valor)
            except ValueError:
                pass
    
    pdf_existe = False
    if documento.pdf_supervisor_assinado:
        try:
            pdf_existe = documento.pdf_supervisor_assinado.storage.exists(documento.pdf_supervisor_assinado.name)
        except Exception:
            pdf_existe = False 

    context = {
        'documento': documento,
        'aluno': request.user,
        'estagio': estagio,
        'dados': dados,
        'pdf_existe': pdf_existe,
    }

    return render(request, template_name, context)


@login_required
@role_required('aluno')
def upload_pdf_assinado(request, documento_id):
    documento = get_object_or_404(DocumentoEstagio, id=documento_id, estagio__aluno=request.user)

    if request.method == 'POST' and 'pdf_supervisor_assinado' in request.FILES:
        documento.pdf_supervisor_assinado = request.FILES['pdf_supervisor_assinado']
        documento.save()
        messages.success(request, 'PDF anexado com sucesso!')
    else:
        messages.error(request, 'Nenhum arquivo foi selecionado.')

    return redirect('visualizar_documento_estagio', documento_id=documento.id)

@login_required
@role_required('aluno')
def remover_pdf_assinado(request, documento_id):
    documento = get_object_or_404(DocumentoEstagio, id=documento_id, estagio__aluno=request.user)

    if request.method == 'POST':
        if documento.pdf_supervisor_assinado:
            documento.pdf_supervisor_assinado.delete(save=True) 
            messages.success(request, "O PDF anexado foi removido com sucesso.")
        else:
            messages.warning(request, "Nenhum PDF estava anexado a este documento.")

    return redirect('visualizar_documento_estagio', documento_id=documento.id)

@login_required
@role_required('aluno')
def assinar_documento_aluno(request, documento_id):
    if request.method != 'POST':
        messages.error(request, "Ação inválida.")
        return redirect('detalhes_estagio_aluno')

    documento = get_object_or_404(DocumentoEstagio, id=documento_id, estagio__aluno=request.user)
    
    if documento.status not in ['RASCUNHO', 'REPROVADO']:
        messages.error(request, "Este documento não está (ou não está mais) aguardando sua ação.")
        return redirect('visualizar_documento_estagio', documento_id=documento.id)

    if documento.tipo_documento == 'TERMO_COMPROMISSO' and not documento.estagio.orientador:
        messages.error(request, "Você precisa 'Editar' e selecionar um Professor Orientador antes de assinar o Termo de Compromisso.")
        return redirect('visualizar_documento_estagio', documento_id=documento.id)
        
    documento.assinado_aluno_em = now()
    documento.assinado_por_aluno = request.user 
    tipo = documento.tipo_documento
    
    if tipo == 'TERMO_COMPROMISSO' or tipo == 'FICHA_PESSOAL':
        documento.status = 'AGUARDANDO_ASSINATURA_PROF'
        
    elif tipo in ['FICHA_IDENTIFICACAO', 'AVALIACAO_SUPERVISOR', 'COMP_RESIDENCIA', 
                  'COMP_AGUA_LUZ', 'ID_CARD', 'SUS_CARD', 'VACINA_CARD', 'APOLICE_SEGURO']:
        documento.status = 'AGUARDANDO_VERIFICACAO_ADMIN'
    else:
        pass 

    documento.save()
    
    if documento.estagio.status_geral == 'RASCUNHO_ALUNO' or documento.estagio.status_geral == 'PENDENTE_CORRECAO':
        documento.estagio.status_geral = 'EM_ANDAMENTO'
        documento.estagio.save()
    
    messages.success(request, "Documento assinado e encaminhado para a próxima etapa!")
    return redirect('visualizar_documento_estagio', documento_id=documento.id)


@login_required
@role_required('aluno')
def preencher_documento_estagio(request, documento_id):
    documento = get_object_or_404(DocumentoEstagio, id=documento_id, estagio__aluno=request.user)
    estagio = documento.estagio 

    if estagio.status_geral != 'RASCUNHO_ALUNO' and documento.status not in ['RASCUNHO', 'REPROVADO']:
        messages.error(request, "Este documento não pode mais ser editado, pois já foi submetido.")
        return redirect('visualizar_documento_estagio', documento_id=documento.id)

    if documento.tipo_documento == 'TERMO_COMPROMISSO':
        FormClass = TermoCompromissoForm
        template_name = 'estagio/docs/TERMO-DE-COMPROMISSO/TERMO-DE-COMPROMISSO_EDITAR.html'
    
    elif documento.tipo_documento == 'FICHA_IDENTIFICACAO':
        FormClass = FichaIdentificacaoForm
        template_name = 'estagio/docs/FICHA-DE-IDENTIFICACAO/FICHA-DE-IDENTIFICACAO_EDITAR.html'
    
    else:
        messages.error(request, f"O preenchimento online para '{documento.get_tipo_documento_display()}' ainda não está disponível.")
        return redirect('detalhes_estagio_aluno')

    if request.method == 'POST':
        if documento.tipo_documento == 'TERMO_COMPROMISSO':
            form = FormClass(request.POST, request.FILES, orientador_initial=estagio.orientador)
        else:
            form = FormClass(request.POST, request.FILES)
        
        
        if form.is_valid():
            dados_para_json = form.cleaned_data.copy()
            if documento.tipo_documento == 'TERMO_COMPROMISSO':
                orientador_selecionado = dados_para_json.pop('orientador', None) 
                
                estagio.orientador = orientador_selecionado
                estagio.supervisor_nome = dados_para_json.get('supervisor_nome', estagio.supervisor_nome)
                estagio.supervisor_empresa = dados_para_json.get('concedente_nome', estagio.supervisor_empresa)
                data_inicio_str = dados_para_json.get('data_inicio')
                data_fim_str = dados_para_json.get('data_fim')
                
                try:
                    if isinstance(data_inicio_str, str):
                        estagio.data_inicio = datetime.date.fromisoformat(data_inicio_str)
                    elif isinstance(data_inicio_str, datetime.date):
                         estagio.data_inicio = data_inicio_str
                         
                    if isinstance(data_fim_str, str):
                        estagio.data_fim = datetime.date.fromisoformat(data_fim_str)
                    elif isinstance(data_fim_str, datetime.date):
                        estagio.data_fim = data_fim_str
                except ValueError:
                    return render(request, template_name, {'form': form, 'documento': documento, 'aluno': request.user, 'estagio': estagio})
                
                estagio.save() 
                
                anexo_pdf = dados_para_json.pop('anexo_assinaturas', None) 
                if anexo_pdf:
                    documento.pdf_supervisor_assinado = anexo_pdf
                elif anexo_pdf is False: 
                    documento.pdf_supervisor_assinado.delete(save=False)
                    documento.pdf_supervisor_assinado = None
                
                if isinstance(dados_para_json.get('data_inicio'), datetime.date):
                    dados_para_json['data_inicio'] = dados_para_json['data_inicio'].isoformat()
                if isinstance(dados_para_json.get('data_fim'), datetime.date):
                    dados_para_json['data_fim'] = dados_para_json['data_fim'].isoformat()
            
            elif documento.tipo_documento == 'FICHA_IDENTIFICACAO':
                foto_3x4_file = dados_para_json.pop('foto_3x4', None)
                
                if foto_3x4_file:
                    documento.foto_3x4 = foto_3x4_file
                elif foto_3x4_file is False: 
                    documento.foto_3x4.delete(save=False) 
                    documento.foto_3x4 = None 
            
            documento.dados_formulario = dados_para_json
            documento.save() 

            messages.success(request, f"'{documento.get_tipo_documento_display()}' salvo como Rascunho!")
            return redirect('visualizar_documento_estagio', documento_id=documento.id)
        else:
            messages.error(request, "Erro ao salvar. Verifique os campos preenchidos.")

    else: 
        initial_data = documento.dados_formulario
        
        if documento.tipo_documento == 'TERMO_COMPROMISSO':
            if not initial_data.get('data_inicio'):
                initial_data['data_inicio'] = estagio.data_inicio
            if not initial_data.get('data_fim'):
                initial_data['data_fim'] = estagio.data_fim
            form = FormClass(initial=initial_data, orientador_initial=estagio.orientador)
        else:
            form = FormClass(initial=initial_data)

    context = {
        'form': form,
        'documento': documento,
        'aluno': request.user, 
        'estagio': estagio 
    }
    return render(request, template_name, context)