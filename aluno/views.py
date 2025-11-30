from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
import datetime
from datetime import date
from core.decorators import role_required
from core.models import Estagio, DocumentoEstagio
from autenticacao.forms import TermoCompromissoForm, FichaIdentificacaoForm, FichaPessoalForm

# === DASHBOARD ===

@login_required
@role_required('aluno')
def aluno_dashboard_view(request):
    aluno = request.user

    return render(request, 'aluno/aluno_dashboard.html', {
        'aluno': aluno
    })


# === ESTÁGIO ===

def is_menor_de_idade(data_nascimento):
    """Verifica se o aluno é menor de 18 anos."""
    if not data_nascimento:
        return True # Se não tiver data, por segurança, consideramos menor (ou exija o preenchimento)
    
    today = date.today()
    # Calcula a idade: ano atual - ano de nascimento - (1 se aniversário deste ano ainda não ocorreu)
    age = today.year - data_nascimento.year - \
        ((today.month, today.day) < (data_nascimento.month, data_nascimento.day))
    
    return age < 18


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
            # Lógica para definir o status inicial correto
            status_inicial = 'RASCUNHO'
            
            # Se for a Avaliação do Orientador, o rascunho pertence ao professor
            if tipo_id == 'AVALIACAO_ORIENTADOR':
                status_inicial = 'RASCUNHO_ORIENTADOR'
            
            documentos_para_criar.append(
                DocumentoEstagio(
                    estagio=estagio,
                    tipo_documento=tipo_id,
                    status=status_inicial 
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
    
    existe_pendencia = documentos_qs.exclude(status='CONCLUIDO').exists()
    
    # Se NÃO houver pendências (tudo verde) E houver documentos na lista
    if not existe_pendencia and documentos_qs.exists():
        # Se o status geral ainda não for APROVADO, atualiza agora
        if estagio.status_geral != 'APROVADO':
            estagio.status_geral = 'APROVADO'
            estagio.save()
    
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

    # 1. Seleção do Template
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
        messages.error(request, "A visualização para este tipo de documento ainda não foi criada.")
        return redirect('detalhes_estagio_aluno')

    # 2. Processamento de Dados do Próprio Documento
    dados = documento.dados_formulario or {}

    # Converter datas do cabeçalho
    for campo in ['data_inicio', 'data_fim']:
        valor = dados.get(campo)
        if isinstance(valor, str):
            try: dados[campo] = datetime.date.fromisoformat(valor)
            except ValueError: pass
            
    # Converter datas da Tabela de Atividades (se houver)
    if 'atividades_lista' in dados:
        for item in dados['atividades_lista']:
            data_str = item.get('data')
            if data_str and isinstance(data_str, str):
                try: item['data'] = datetime.date.fromisoformat(data_str)
                except ValueError: pass
            
    # 3. BUSCAR DADOS DO TERMO (Necessário para Ficha Pessoal E Avaliação)
    dados_termo = {}
    if documento.tipo_documento in ['FICHA_PESSOAL', 'AVALIACAO_ORIENTADOR', 'AVALIACAO_SUPERVISOR']:
        try:
            termo = DocumentoEstagio.objects.filter(
                estagio=estagio, 
                tipo_documento='TERMO_COMPROMISSO'
            ).first()
            if termo:
                dados_termo = termo.dados_formulario or {}
                # Converter datas do termo para visualização correta
                for key in ['data_inicio', 'data_fim']:
                    if dados_termo.get(key):
                        try: dados_termo[key] = datetime.date.fromisoformat(dados_termo[key])
                        except: pass
        except Exception:
            pass
    
    # 4. BUSCAR DADOS REAIS DA FICHA PESSOAL (Necessário para Avaliação)
    dados_reais = {}
    if documento.tipo_documento in ['AVALIACAO_ORIENTADOR', 'AVALIACAO_SUPERVISOR']:
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

    # 5. Verificação de Arquivos Anexos (PDF Assinado)
    pdf_existe = False
    if documento.pdf_supervisor_assinado:
        try:
            pdf_existe = documento.pdf_supervisor_assinado.storage.exists(documento.pdf_supervisor_assinado.name)
        except Exception:
            pdf_existe = False 

    aluno = request.user
    is_menor = is_menor_de_idade(request.user.data_nascimento)
    
    context = {
        'documento': documento,
        'aluno': request.user,
        'estagio': estagio,
        'dados': dados,
        'dados_termo': dados_termo, # Envia dados do Termo
        'dados_reais': dados_reais, # Envia dados da Ficha (Datas reais e Horas)
        'pdf_existe': pdf_existe,
        'is_menor': is_menor,
    }

    return render(request, template_name, context)


@login_required
@role_required('aluno')
def upload_arquivo_anexo(request, documento_id):
    """
    Função genérica para fazer upload no campo 'arquivo_anexo' (RG, CPF, etc.)
    Diferente do 'upload_pdf_assinado' que é para documentos gerados pelo sistema.
    """
    documento = get_object_or_404(DocumentoEstagio, id=documento_id, estagio__aluno=request.user)

    if request.method == 'POST' and 'arquivo_anexo' in request.FILES:
        file = request.FILES['arquivo_anexo']
        
        # Validação simples de extensão (opcional)
        if not file.name.lower().endswith('.pdf'):
             messages.error(request, "Apenas arquivos PDF são permitidos.")
             return redirect('visualizar_documento_estagio', documento_id=documento.id)

        documento.arquivo_anexo = file
        documento.save()
        messages.success(request, 'Arquivo anexado com sucesso!')
    else:
        messages.error(request, 'Nenhum arquivo selecionado.')

    return redirect('visualizar_documento_estagio', documento_id=documento.id)

@login_required
@role_required('aluno')
def remover_arquivo_anexo(request, documento_id):
    documento = get_object_or_404(DocumentoEstagio, id=documento_id, estagio__aluno=request.user)

    if request.method == 'POST':
        if documento.arquivo_anexo:
            documento.arquivo_anexo.delete(save=True)
            messages.success(request, "Arquivo removido com sucesso.")
        else:
            messages.warning(request, "Nenhum arquivo para remover.")

    return redirect('visualizar_documento_estagio', documento_id=documento.id)

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
    aluno = request.user

    # -------------------------------------------------------------
    # 1. RESTRIÇÃO SOMENTE PARA TERMO DE COMPROMISSO (menor de idade)
    # -------------------------------------------------------------
    if documento.tipo_documento == 'TERMO_COMPROMISISSO':
        if is_menor_de_idade(aluno.data_nascimento):
            messages.error(
                request,
                "Alunos menores de idade NÃO podem usar a Assinatura Eletrônica no Termo de Compromisso. "
                "Por favor, anexe o PDF assinado pelo responsável e clique em 'Encaminhar ao Professor'."
            )
            return redirect('visualizar_documento_estagio', documento_id=documento.id)

        # Maior de idade: validar se o PDF do supervisor está anexado
        if not documento.pdf_supervisor_assinado:
            messages.error(
                request,
                "Você deve anexar o PDF do Termo assinado pelo Supervisor antes de assinar eletronicamente."
            )
            return redirect('visualizar_documento_estagio', documento_id=documento.id)

    # -------------------------------------------------------------
    # 2. CONFERIR STATUS PERMITIDO PARA ASSINAR
    # -------------------------------------------------------------
    if documento.status not in ['RASCUNHO', 'REPROVADO']:
        messages.error(request, "Este documento não está aguardando sua assinatura.")
        return redirect('visualizar_documento_estagio', documento_id=documento.id)

    # -------------------------------------------------------------
    # 3. VALIDAÇÕES ESPECÍFICAS PARA O TERMO DE COMPROMISSO
    # -------------------------------------------------------------
    dados = documento.dados_formulario or {}
    erros = []

    if documento.tipo_documento == 'TERMO_COMPROMISSO':
        campos_obrigatorios = [
            'concedente_nome', 'concedente_cnpj', 'concedente_rua', 'concedente_numero',
            'concedente_bairro', 'concedente_cidade_uf', 'concedente_cep',
            'concedente_telefone', 'concedente_representante', 'concedente_email',
            'supervisor_nome', 'data_inicio', 'data_fim', 'carga_horaria_diaria',
            'carga_horaria_semanal', 'apolice_numero', 'apolice_empresa'
        ]

        for campo in campos_obrigatorios:
            if not dados.get(campo):
                erros.append("Há campos obrigatórios não preenchidos no Termo.")
                break

        if not documento.estagio.orientador:
            erros.append("Você precisa selecionar o Professor Orientador antes de assinar.")

    if erros:
        for erro in erros:
            messages.error(request, erro)
        return redirect('visualizar_documento_estagio', documento_id=documento.id)

    # -------------------------------------------------------------
    # 4. REALIZAR ASSINATURA DO ALUNO
    # -------------------------------------------------------------
    documento.assinado_aluno_em = now()
    documento.assinado_por_aluno = aluno
    tipo = documento.tipo_documento

    # -------------------------------------------------------------
    # 5. DEFINIR PRÓXIMO STATUS
    # -------------------------------------------------------------
    if tipo == 'TERMO_COMPROMISSO':
        # Maior de idade → assina e já encaminha automaticamente
        documento.status = 'AGUARDANDO_ASSINATURA_PROF'

    elif tipo == 'FICHA_PESSOAL':
        documento.status = 'AGUARDANDO_ASSINATURA_PROF'

    else:
        documento.status = 'AGUARDANDO_VERIFICACAO_ADMIN'

    documento.save()

    # -------------------------------------------------------------
    # 6. ATUALIZA STATUS GERAL DO ESTÁGIO
    # -------------------------------------------------------------
    if documento.estagio.status_geral in ['RASCUNHO_ALUNO', 'PENDENTE_CORRECAO']:
        documento.estagio.status_geral = 'EM_ANDAMENTO'
        documento.estagio.save()

    messages.success(request, "Documento assinado e encaminhado para a próxima etapa!")
    return redirect('visualizar_documento_estagio', documento_id=documento.id)


@login_required
@role_required('aluno')
def encaminhar_documento_aluno(request, documento_id):
    if request.method != 'POST':
        messages.error(request, "Ação inválida.")
        return redirect('detalhes_estagio_aluno')

    documento = get_object_or_404(DocumentoEstagio, id=documento_id, estagio__aluno=request.user)
    
    if documento.status not in ['RASCUNHO', 'REPROVADO']:
        messages.error(request, "Este documento não está em rascunho ou reprovado, e não pode ser encaminhado.")
        return redirect('visualizar_documento_estagio', documento_id=documento.id)

    # 1. VALIDAÇÃO ESPECÍFICA PARA O TERMO
    if documento.tipo_documento == 'TERMO_COMPROMISSO':
        if not documento.estagio.orientador:
            messages.error(request, "Você precisa selecionar um Professor Orientador no formulário antes de encaminhar.")
            return redirect('visualizar_documento_estagio', documento_id=documento.id)
        
        # O aluno menor de idade SÓ PODE encaminhar se o PDF assinado estiver anexado.
        if not documento.pdf_supervisor_assinado:
            messages.error(request, "Você deve anexar o PDF do Termo de Compromisso assinado pelo Supervisor (ou Responsável) antes de encaminhar.")
            return redirect('visualizar_documento_estagio', documento_id=documento.id)

    # 2. LÓGICA DE ENCAMINHAMENTO COM TRATAMENTO DE ERRO
    try:
        # Marca a data da ação do aluno (Encaminhamento)
        # Assumindo que usa assinado_aluno_em para a data da ação do aluno.
        documento.data_encaminhamento_aluno = now()

        # Define o próximo status
        if documento.tipo_documento in ['TERMO_COMPROMISSO', 'FICHA_PESSOAL']:
            documento.status = 'AGUARDANDO_ASSINATURA_PROF'
        elif documento.tipo_documento in ['FICHA_IDENTIFICACAO', 'AVALIACAO_SUPERVISOR', 'COMP_RESIDENCIA', 
                                         'COMP_AGUA_LUZ', 'ID_CARD', 'SUS_CARD', 'VACINA_CARD', 'APOLICE_SEGURO']:
            documento.status = 'AGUARDANDO_VERIFICACAO_ADMIN'
        else:
            documento.status = 'AGUARDANDO_VERIFICACAO_ADMIN'
        
        documento.save()
        
        # Atualiza o status geral do estágio se for o primeiro envio
        if documento.estagio.status_geral in ['RASCUNHO_ALUNO', 'PENDENTE_CORRECAO']:
            documento.estagio.status_geral = 'EM_ANDAMENTO'
            documento.estagio.save()

        messages.success(request, f"Documento '{documento.get_tipo_documento_display()}' encaminhado para a próxima etapa!")
    
    except Exception as e:
        # Se ocorrer um erro no save, a mensagem será exibida.
        messages.error(request, f"Erro inesperado ao encaminhar o documento. Detalhe: {e}")
        
    return redirect('visualizar_documento_estagio', documento_id=documento.id)


@login_required
@role_required('aluno')
def preencher_documento_estagio(request, documento_id):
    documento = get_object_or_404(DocumentoEstagio, id=documento_id, estagio__aluno=request.user)
    estagio = documento.estagio 
    
    if documento.tipo_documento == 'AVALIACAO_ORIENTADOR':
        messages.warning(request, "Este documento deve ser preenchido pelo seu Professor Orientador.")
        return redirect('visualizar_documento_estagio', documento_id=documento.id)

    if estagio.status_geral != 'RASCUNHO_ALUNO' and documento.status not in ['RASCUNHO', 'REPROVADO']:
        messages.error(request, "Este documento não pode mais ser editado, pois já foi submetido.")
        return redirect('visualizar_documento_estagio', documento_id=documento.id)

    # Seleção do Formulário e Template
    if documento.tipo_documento == 'TERMO_COMPROMISSO':
        FormClass = TermoCompromissoForm
        template_name = 'estagio/docs/TERMO-DE-COMPROMISSO/TERMO-DE-COMPROMISSO_EDITAR.html'
    
    elif documento.tipo_documento == 'FICHA_IDENTIFICACAO':
        FormClass = FichaIdentificacaoForm
        template_name = 'estagio/docs/FICHA-DE-IDENTIFICACAO/FICHA-DE-IDENTIFICACAO_EDITAR.html'
        
    elif documento.tipo_documento == 'FICHA_PESSOAL':
        FormClass = FichaPessoalForm
        template_name = 'estagio/docs/FICHA-PESSOAL/FICHA-PESSOAL_EDITAR.html'
    
    else:
        messages.error(request, f"O preenchimento online para '{documento.get_tipo_documento_display()}' ainda não está disponível.")
        return redirect('detalhes_estagio_aluno')

    if request.method == 'POST':
        # Inicializa o formulário com os dados enviados
        if documento.tipo_documento == 'TERMO_COMPROMISSO':
            form = FormClass(request.POST, request.FILES, orientador_initial=estagio.orientador)
        else:
            form = FormClass(request.POST, request.FILES)
        
        # O form.is_valid() agora deve passar sempre (devido ao nosso hack no forms.py)
        if form.is_valid():
            dados_para_json = form.cleaned_data.copy()
            
            # === 1. CONVERSÃO CRÍTICA DE DATAS PARA STRING ===
            # O JSON não aceita objetos 'date' do Python. Convertemos para texto ISO aqui.
            for key, value in dados_para_json.items():
                if isinstance(value, (datetime.date, datetime.datetime)):
                    dados_para_json[key] = value.isoformat()
            # =================================================

            # === 2. LÓGICA ESPECÍFICA: TERMO DE COMPROMISSO ===
            if documento.tipo_documento == 'TERMO_COMPROMISSO':
                orientador_selecionado = dados_para_json.pop('orientador', None) 
                
                # Atualiza o orientador no Estágio
                estagio.orientador = orientador_selecionado
                
                # CORREÇÃO DO INTEGRITY ERROR:
                # Se o campo estiver vazio, salva um texto padrão para não quebrar o banco de dados
                estagio.supervisor_nome = dados_para_json.get('supervisor_nome') or "(Ainda não definido)"
                estagio.supervisor_empresa = dados_para_json.get('concedente_nome') or "(Ainda não definido)"
                
                # Atualiza datas no Estágio (Modelo Principal)
                data_inicio_str = dados_para_json.get('data_inicio')
                data_fim_str = dados_para_json.get('data_fim')
                
                try:
                    if data_inicio_str:
                        estagio.data_inicio = datetime.date.fromisoformat(data_inicio_str)
                    if data_fim_str:
                        estagio.data_fim = datetime.date.fromisoformat(data_fim_str)
                except ValueError:
                    # Se a data for inválida, não crasha, apenas ignora a atualização no modelo Estagio
                    pass
                
                estagio.save() 
                
                # Processamento do Anexo PDF (Assinaturas Manuais)
                anexo_pdf = dados_para_json.pop('anexo_assinaturas', None) 
                if anexo_pdf:
                    documento.pdf_supervisor_assinado = anexo_pdf
                elif anexo_pdf is False: # Checkbox de limpar foi marcado (se houver)
                    documento.pdf_supervisor_assinado.delete(save=False)
                    documento.pdf_supervisor_assinado = None
            
            # === 3. LÓGICA ESPECÍFICA: FICHA DE IDENTIFICAÇÃO ===
            elif documento.tipo_documento == 'FICHA_IDENTIFICACAO':
                foto_3x4_file = dados_para_json.pop('foto_3x4', None)
                
                if foto_3x4_file:
                    documento.foto_3x4 = foto_3x4_file
                elif foto_3x4_file is False: 
                    documento.foto_3x4.delete(save=False) 
                    documento.foto_3x4 = None 
            
            # === 4. LÓGICA ESPECÍFICA: FICHA PESSOAL (TABELA DINÂMICA) ===
            elif documento.tipo_documento == 'FICHA_PESSOAL':
                # Salva os campos normais do form primeiro (cabeçalho)
                documento.dados_formulario = dados_para_json
                
                # Captura as listas manuais da tabela HTML
                datas = request.POST.getlist('atividade_data')
                atividades = request.POST.getlist('atividade_desc')
                objetivos = request.POST.getlist('atividade_obj')
                horarios = request.POST.getlist('atividade_horario')
                qtd_horas = request.POST.getlist('atividade_qtd_horas') 
                
                lista_atividades = []
                
                # Agrupa tudo numa lista de dicionários
                for d, a, o, h, q in zip(datas, atividades, objetivos, horarios, qtd_horas):
                    # Só salva a linha se tiver pelo menos um dado preenchido
                    if d or a or o or h: 
                        lista_atividades.append({
                            'data': d,
                            'atividade': a,
                            'objetivo': o,
                            'horario': h,
                            'qtd_horas': q
                        })
                
                # Adiciona a lista processada ao JSON final
                documento.dados_formulario['atividades_lista'] = lista_atividades

            # === 5. SALVAMENTO FINAL ===
            # Para documentos que não são Ficha Pessoal, atualizamos o JSON aqui.
            # (A Ficha Pessoal já foi atualizada dentro do bloco elif acima)
            if documento.tipo_documento != 'FICHA_PESSOAL':
                 documento.dados_formulario = dados_para_json

            documento.save() 

            messages.success(request, f"'{documento.get_tipo_documento_display()}' salvo como Rascunho!")
            return redirect('visualizar_documento_estagio', documento_id=documento.id)
        else:
            messages.error(request, "Erro ao salvar. Verifique os campos preenchidos.")

    else: 
        # GET Request: Prepara o formulário com dados existentes
        initial_data = documento.dados_formulario
        
        if documento.tipo_documento == 'TERMO_COMPROMISSO':
            # Se não tiver datas no JSON, usa as do Estágio
            if not initial_data.get('data_inicio'):
                initial_data['data_inicio'] = estagio.data_inicio
            if not initial_data.get('data_fim'):
                initial_data['data_fim'] = estagio.data_fim
            form = FormClass(initial=initial_data, orientador_initial=estagio.orientador)
        else:
            form = FormClass(initial=initial_data)
            
    # === Lógica para pré-carregar dados do Termo na Ficha Pessoal (Visualização Auxiliar) ===
    dados_termo = {}
    if documento.tipo_documento == 'FICHA_PESSOAL':
        try:
            termo = DocumentoEstagio.objects.filter(
                estagio=estagio, 
                tipo_documento='TERMO_COMPROMISSO'
            ).first()
            if termo:
                dados_termo = termo.dados_formulario or {}
        except Exception:
            pass
    # ================================================================

    context = {
        'form': form,
        'documento': documento,
        'aluno': request.user, 
        'estagio': estagio,
        'dados': documento.dados_formulario or {}, 
        'dados_termo': dados_termo
    }
    return render(request, template_name, context)