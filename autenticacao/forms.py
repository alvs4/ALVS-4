from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, get_user_model
from django.forms import modelformset_factory, BaseModelFormSet
from core.models import Turma, AlunoTurma, ProfessorMateriaAnoCursoModalidade, Curso, Estagio
import datetime
import random

CustomUser = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuário",
        widget=forms.TextInput(attrs={'autofocus': True, 'name': 'username', 'class': 'form-control'})
    )
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )
        return self.cleaned_data
    
class InserirEmailForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "exemplo@email.com"
        })
    )
    
class Codigo2FAForm(forms.Form):
    codigo = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Digite o código recebido"}),
    )
    
class ProfessorMateriaAnoCursoModalidadeForm(forms.ModelForm):
    class Meta:
        model = ProfessorMateriaAnoCursoModalidade
        fields = ['materia', 'curso', 'ano_modulo', 'modalidade']
        labels = {
            'materia': 'Matéria',
            'curso': 'Curso',
            'ano_modulo': 'Ano/Módulo',
            'modalidade': 'Modalidade',
        }
        widgets = {
            'materia': forms.Select(attrs={'class': 'form-select'}),
            'curso': forms.Select(attrs={'class': 'form-select'}),
            'ano_modulo': forms.Select(attrs={'class': 'form-select'}),
            'modalidade': forms.Select(attrs={'class': 'form-select'}),
        }

class RequiredIdFormSet(BaseModelFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if 'id' in form.fields:
            form.fields['id'].required = False

ProfessorMateriaAnoCursoModalidadeFormSet = modelformset_factory(
    ProfessorMateriaAnoCursoModalidade,
    form=ProfessorMateriaAnoCursoModalidadeForm,
    extra=3,
    can_delete=True,
    formset=RequiredIdFormSet
)

class AlunoCreateForm(forms.ModelForm):
    curso = forms.ModelChoiceField(
        queryset=Curso.objects.all().order_by('nome'),
        label="1. Escolha o Curso",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    ano_modulo = forms.ChoiceField(
        label="2. Escolha o Ano/Módulo",
        choices=[('', '---------')], 
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    turno = forms.ChoiceField(
        label="3. Escolha o Turno",
        choices=[('', '---------')], 
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    turma = forms.ModelChoiceField(
        queryset=Turma.objects.none(), 
        label="4. Escolha a Turma",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name',
            'data_nascimento', 'cidade_nascimento',
            'rg', 'orgao', 'data_expedicao', 'cpf',
            'nome_pai', 'nome_mae', 'responsavel_matricula',
            'endereco_rua', 'endereco_numero', 'endereco_bairro',
            'endereco_cidade', 'endereco_cep', 'telefone',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['turma'].label_from_instance = lambda obj: obj.nome_curto

        if 'curso' in self.data:
            try:
                curso_id = int(self.data.get('curso'))
                self.fields['ano_modulo'].choices = [('', '---------')] + list(Turma.objects.filter(curso_id=curso_id).order_by('ano_modulo').values_list('ano_modulo', 'ano_modulo').distinct())
                
                if 'ano_modulo' in self.data:
                    ano_modulo_val = self.data.get('ano_modulo')
                    self.fields['turno'].choices = [('', '---------')] + list(Turma.objects.filter(curso_id=curso_id, ano_modulo=ano_modulo_val).values_list('turno', 'turno').distinct())
                    
                    if 'turno' in self.data:
                        turno_val = self.data.get('turno')
                        self.fields['turma'].queryset = Turma.objects.filter(curso_id=curso_id, ano_modulo=ano_modulo_val, turno=turno_val).order_by('turma')
            except (ValueError, TypeError):
                pass 
        if self.instance and self.instance.pk:
            try:
                turma_atual = self.instance.alunoturma_set.first().turma
                if turma_atual:
                    self.fields['curso'].initial = turma_atual.curso
                    
                    anos_queryset = Turma.objects.filter(curso=turma_atual.curso).values_list('ano_modulo', 'ano_modulo').distinct()
                    self.fields['ano_modulo'].choices = [('', '---------')] + list(anos_queryset)
                    self.fields['ano_modulo'].initial = turma_atual.ano_modulo
                    
                    turnos_queryset = Turma.objects.filter(curso=turma_atual.curso, ano_modulo=turma_atual.ano_modulo).values_list('turno', flat=True).distinct()
                    self.fields['turno'].choices = [('', '---------')] + [(v, d) for v, d in Turma.TURNO_CHOICES if v in turnos_queryset]
                    self.fields['turno'].initial = turma_atual.turno
                    
                    self.fields['turma'].queryset = Turma.objects.filter(pk=turma_atual.pk)
                    self.fields['turma'].initial = turma_atual
            except (AttributeError, Exception):
                pass

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '')
        return ''.join(filter(str.isdigit, cpf))

    def clean_rg(self):
        rg = self.cleaned_data.get('rg', '')
        return ''.join(filter(str.isdigit, rg))

    def save(self, commit=True):
        aluno = super().save(commit=False)
        aluno.tipo = 'aluno'
        
        # (Esta lógica está correta, não gera senha/matrícula ao editar)
        if not aluno.pk:
            ano = datetime.date.today().year
            aleatorio = ''.join(str(random.randint(0, 9)) for _ in range(8))
            aluno.numero_matricula = f"{ano}{aleatorio}"
            aluno.username = aluno.numero_matricula
            aluno.set_password("Senha123#")
            aluno.senha_temporaria = True

        if commit:
            aluno.save()
            turma_selecionada = self.cleaned_data.get('turma')
            if turma_selecionada:
                AlunoTurma.objects.update_or_create(
                    aluno=aluno,
                    defaults={'turma': turma_selecionada}
                )
        return aluno


class ProfessorCreateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name',
            'data_nascimento',          
            'cidade_nascimento',
            'rg',
            'orgao',
            'data_expedicao',
            'cpf',
            'nome_pai',
            'nome_mae',
            'endereco_rua',
            'endereco_numero',
            'endereco_bairro',
            'endereco_cidade',
            'endereco_cep',
            'telefone',
        ]

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '')
        return ''.join(filter(str.isdigit, cpf))

    def clean_rg(self):
        rg = self.cleaned_data.get('rg', '')
        return ''.join(filter(str.isdigit, rg))

    def save(self, commit=True):
        professor = super().save(commit=False)
        professor.tipo = 'professor'
        
        # 🎯 CORREÇÃO: Adicionada a verificação 'if not professor.pk'
        # para não gerar nova senha/matrícula ao editar
        if not professor.pk:
            ano = datetime.date.today().year
            aleatorio = ''.join(str(random.randint(0, 9)) for _ in range(8))
            professor.numero_matricula = f"{ano}{aleatorio}"
            professor.username = professor.numero_matricula
            professor.set_password("Senha123#")
            professor.senha_temporaria = True

        if commit:
            professor.save()
        return professor


class ServidorCreateForm(forms.ModelForm):
    # 🎯 CORREÇÃO: 'direcao' está correto, alinhado com o models.py
    TIPO_USUARIO_CHOICES = (
        ('', '---------'),
        ('servidor', 'Administrativo'),
        ('direcao', 'Direção'),
    )
    tipo_usuario = forms.ChoiceField(
        choices=TIPO_USUARIO_CHOICES,
        label="Tipo de Usuário",
        required=True
    )

    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'eixo',
            'data_nascimento', 'cidade_nascimento', 'cpf', 'rg', 'orgao', 'data_expedicao',
            'nome_mae', 'nome_pai',
            'telefone', 'endereco_cep', 'endereco_cidade', 'endereco_bairro', 'endereco_rua', 'endereco_numero',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'eixo' in self.fields:
            self.fields['eixo'].required = False
        
        # 🎯 CORREÇÃO: Esta ordenação agora funciona
        field_order = ['tipo_usuario', 'eixo', 'first_name', 'last_name', 'cpf', 'rg']
        self.order_fields(field_order)

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf', '')
        return ''.join(filter(str.isdigit, cpf))

    def clean_rg(self):
        rg = self.cleaned_data.get('rg', '')
        return ''.join(filter(str.isdigit, rg))

    def save(self, commit=True):
        servidor = super().save(commit=False)
        
        # 🎯 CORREÇÃO: Adicionada a verificação 'if not servidor.pk'
        # para não gerar nova senha/matrícula ao editar
        if not servidor.pk:
            ano = datetime.date.today().year
            aleatorio = ''.join(str(random.randint(0, 9)) for _ in range(8))
            servidor.numero_matricula = f"{ano}{aleatorio}"
            servidor.username = servidor.numero_matricula
            servidor.set_password("Senha123#")
            servidor.senha_temporaria = True

        if commit:
            servidor.save()
        return servidor
    
# 🎯 REMOVIDO: 'EstagioCreateForm' foi removido
# Esta classe tornou-se obsoleta. A 'gestao_estagio_aluno' (view)
# agora cria o Estagio, e o 'TermoCompromissoForm' (abaixo)
# é usado para preencher os dados.


class ProfessorOrientadorChoiceField(forms.ModelChoiceField):
    """
    Campo customizado que muda como o nome do professor é exibido.
    Ex: "Alex Barbosa - Informática (Internet)"
    """
    def label_from_instance(self, obj):
        prof_name = obj.get_full_name()
        
        vinculo = obj.professormateriaanocursomodalidade_set.select_related('materia', 'curso').first()
        
        if vinculo:
            details = f"{vinculo.materia.nome} ({vinculo.curso.nome})"
            return f"{prof_name} - {details}"
        else:
            return f"{prof_name} - (Sem vínculos cadastrados)"
        

class TermoCompromissoForm(forms.Form):
    """
    Este formulário representa os campos EDITÁVEIS
    do documento TERMO-DE-COMPROMISSO.html.
    Todos os campos foram configurados como opcionais no __init__
    e no método clean para permitir o salvamento de rascunhos.
    """
    
    # Dados da Empresa (Concedente)
    concedente_nome = forms.CharField(label="Nome da Concedente (Empresa)")
    concedente_cnpj = forms.CharField(label="CNPJ da Concedente")
    concedente_rua = forms.CharField(label="Rua", max_length=150)
    concedente_numero = forms.CharField(label="Nº", max_length=10)
    concedente_bairro = forms.CharField(label="Bairro", max_length=100)
    concedente_cidade_uf = forms.CharField(label="Cidade-UF", max_length=100) 
    concedente_cep = forms.CharField(label="CEP", max_length=9) 
    concedente_representante = forms.CharField(label="Nome do Representante da Concedente")
    concedente_email = forms.EmailField(label="Email da Concedente")
    concedente_telefone = forms.CharField(label="Telefone da Concedente")

    # Dados do Supervisor
    supervisor_nome = forms.CharField(label="Nome do Supervisor (funcionário da Concedente)")

    # Dados do Estágio
    data_inicio = forms.DateField(label="Data de Início (___/___/____)", widget=forms.DateInput(attrs={'type': 'date'}))
    data_fim = forms.DateField(label="Data de Término (___/___/____)", widget=forms.DateInput(attrs={'type': 'date'}))
    carga_horaria_diaria = forms.IntegerField(label="Horas Diárias", min_value=1, max_value=8)
    carga_horaria_semanal = forms.IntegerField(label="Horas Semanais", min_value=1, max_value=40)
    
    # Dados da Apólice de Seguro
    apolice_numero = forms.CharField(label="Nº da Apólice de Seguro")
    apolice_empresa = forms.CharField(label="Nome da Seguradora")
    
    # Campo Orientador
    orientador = ProfessorOrientadorChoiceField(
        queryset=CustomUser.objects.filter(tipo='professor').order_by('first_name', 'last_name'),
        label="Professor(a) Orientador(a) da Escola",
        required=True, # Será sobrescrito no __init__
        empty_label="-- Selecione o Professor --",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'}) 
    )

    # Campo Anexo PDF
    anexo_assinaturas = forms.FileField(
        label="Anexar PDF (com assinaturas do Supervisor/Responsável)",
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'})
    )
    
    # MÉTODO __init__
    def __init__(self, *args, **kwargs):
        orientador_initial = kwargs.pop('orientador_initial', None)
        super().__init__(*args, **kwargs)
        
        # Percorre todos os campos do formulário
        for field_name, field in self.fields.items():
            
            # 1. Torna todos os campos opcionais na definição do campo
            field.required = False
            
            if field_name not in ['orientador', 'anexo_assinaturas']: 
                attrs = {'class': 'inline-input'}
                
                if field_name == 'concedente_cep':
                     attrs['data-mask'] = '00000-000'
                elif 'data' in field_name:
                    attrs['type'] = 'date'
                elif isinstance(field, forms.IntegerField):
                    attrs['type'] = 'number'
                
                if self.errors.get(field_name):
                    attrs['class'] += ' is-invalid' 
                
                field.widget.attrs.update(attrs)
            
            elif field_name == 'orientador' and orientador_initial:
                 self.initial['orientador'] = orientador_initial

    # === NOVO MÉTODO CLEAN (A SOLUÇÃO) ===
    def clean(self):
        """
        Limpa erros de validação para campos vazios.
        Isso força o Django a aceitar o formulário como válido mesmo que
        campos numéricos ou de data estejam em branco ou inválidos.
        """
        cleaned_data = super().clean()
        
        # Lista de campos que deram erro
        campos_com_erro = list(self.errors.keys())
        
        for field in campos_com_erro:
            # Verifica o valor enviado pelo usuário (raw data)
            valor_enviado = self.data.get(field)
            
            # Se o valor for vazio, None ou uma string vazia
            if not valor_enviado:
                # Remove o erro da lista de erros do formulário
                del self._errors[field]
                
                # Garante que no cleaned_data o valor seja None (para salvar no banco sem quebrar)
                if field in cleaned_data:
                    cleaned_data[field] = None
                else:
                    cleaned_data[field] = None
                    
        return cleaned_data
                 
class FichaIdentificacaoForm(forms.Form):
    """
    Formulário para os campos preenchíveis da Ficha de Identificação.
    Permite salvar rascunhos incompletos.
    """
    ATIVIDADE_CHOICES = (
        ('NENHUMA', 'Não Possui'),
        ('AUTONOMO', 'Autônomo'),
        ('EMPREGADO', 'Empregado'),
    )

    atividade_tipo = forms.ChoiceField(
        choices=ATIVIDADE_CHOICES,
        label="Autônomo/ Empregado",
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='NENHUMA'
    )
    
    atividade_carga_horaria = forms.CharField(
        label="Carga Horária (Ex: 20h/semana)", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    atividade_empresa = forms.CharField(
        label="Empresa", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    atividade_funcao = forms.CharField(
        label="Função", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    
    # Endereço da Atividade
    atividade_rua = forms.CharField(
        label="Rua/ Av./ Pça", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    atividade_numero = forms.CharField(
        label="N°", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    atividade_bairro = forms.CharField(
        label="Bairro", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    atividade_cidade = forms.CharField(
        label="Cidade", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    atividade_cep = forms.CharField(
        label="CEP", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': '00000-000'})
    )
    
    foto_3x4 = forms.ImageField(
        label="Foto 3x4 (Opcional)",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control form-control-sm'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna todos os campos opcionais para permitir Rascunho
        for field in self.fields.values():
            field.required = False

    def clean(self):
        cleaned_data = super().clean()
        
        # 1. Lógica de Limpeza de Erros (Rascunho)
        erros_para_remover = []
        for field, errors in self.errors.items():
            valor = self.data.get(field)
            # Se estiver vazio, remove o erro (permite salvar vazio)
            if not valor:
                erros_para_remover.append(field)
        
        for field in erros_para_remover:
            del self._errors[field]
            if field in cleaned_data:
                cleaned_data[field] = None

        # 2. Lógica de Negócio (Só valida se for submissão final, opcionalmente)
        # Mantemos a lógica original de limpar campos se for 'NENHUMA'
        atividade_tipo = cleaned_data.get('atividade_tipo')
        if atividade_tipo == 'NENHUMA':
            campos_atividade = [
                'atividade_carga_horaria', 'atividade_empresa', 'atividade_funcao',
                'atividade_rua', 'atividade_numero', 'atividade_bairro', 
                'atividade_cidade', 'atividade_cep'
            ]
            for campo in campos_atividade:
                cleaned_data[campo] = ''
                
        return cleaned_data
    
class FichaPessoalForm(forms.Form):
    # Dados do Estágio / Cabeçalho
    data_inicio = forms.DateField(
        label="Início do Estágio", 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    data_fim = forms.DateField(
        label="Fim do Estágio", 
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    
    # Dados da Concedente (Empresa)
    concedente_nome = forms.CharField(
        label="Concedente (Empresa)", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    concedente_municipio = forms.CharField(
        label="Município", 
        initial="Guanambi",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    concedente_cnpj = forms.CharField(
        label="CNPJ",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-mask': '00.000.000/0000-00'})
    )
    concedente_email = forms.EmailField(
        label="E-mail da Empresa",
        widget=forms.EmailInput(attrs={'class': 'form-control form-control-sm'})
    )
    
    # Dados do Supervisor
    supervisor_nome = forms.CharField(
        label="Nome do Supervisor", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    supervisor_telefone = forms.CharField(
        label="Telefone do Supervisor", 
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'})
    )
    
    total_horas = forms.CharField(
        label="Total de Horas Cumpridas",
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Ex: 100 horas'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Torna todos os campos opcionais
        for field in self.fields.values():
            field.required = False

    def clean(self):
        cleaned_data = super().clean()
        
        # Limpa erros de validação para campos vazios (Rascunho)
        erros_para_remover = []
        for field in self.errors:
            if not self.data.get(field):
                erros_para_remover.append(field)
        
        for field in erros_para_remover:
            if field in self._errors:
                del self._errors[field]
            if field in cleaned_data:
                cleaned_data[field] = None
                
        return cleaned_data
    
class AvaliacaoOrientadorForm(forms.Form):
    OPCOES_AVALIACAO = [
        ('OTIMO', 'Ótimo'),
        ('BOM', 'Bom'),
        ('REGULAR', 'Regular'),
        ('INSUFICIENTE', 'Insuficiente'),
    ]

    # Tabela 1: Avaliação da Concedente (Empresa)
    infraestrutura = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    atividades_exercidas = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    organizacao_empresa = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    supervisao_estagio = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    avaliacao_final_empresa = forms.CharField(label="Avaliação Final (Nota)", required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'style': 'width: 100px;'}))

    total_horas = forms.CharField(label="Total de Horas Cumpridas", required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-sm'}))

    # Tabela 2: Avaliação do Estagiário (Aspectos)
    assiduidade = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    pontualidade = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    interesse = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    organizacao_aluno = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    responsabilidade = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    postura = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    relacionamento = forms.ChoiceField(choices=OPCOES_AVALIACAO, widget=forms.RadioSelect, required=False)
    avaliacao_final_aluno = forms.CharField(label="Avaliação Final (Nota)", required=False, widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'style': 'width: 100px;'}))

    observacoes = forms.CharField(label="Observações", required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    def clean(self):
        # (A mesma lógica de limpeza que usamos nos outros forms)
        cleaned_data = super().clean()
        erros_para_remover = []
        for field in self.errors:
            if not self.data.get(field):
                erros_para_remover.append(field)
        for field in erros_para_remover:
            if field in self._errors: del self._errors[field]
            if field in cleaned_data: cleaned_data[field] = None
        return cleaned_data