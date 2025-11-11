# Em core/management/commands/seed_grade.py

from django.core.management.base import BaseCommand
from core.models import Curso, Materia, GradeMateria
from django.db import IntegrityError
import sys

# ======================================================================
# 1. LISTA MESTRA DA BASE COMUM
# Nomes normalizados (MAIÚSCULOS) do seed_materias_completo.py
# ======================================================================
MATERIAS_BASE_COMUM = {
    "LP E LITERATURA", "LP E R", "LINGUA", "TECNICAS DE REDAÇÃO", "REDAÇÃO INSTRUMENTAL", "PORTUG",
    "MATEMATICA",
    "QUIMICA",
    "BIOLOGIA", "BIOLOG",
    "FISICA",
    "GEOGRAFIA",
    "HISTÓRIA", "HISTORIA",
    "FILOSOFIA", "FILOSO",
    "SOCIOLOGIA",
    "INGLÊS", "INGLES",
    "ARTE",
    "EDUCAÇÃO FÍSICA", "EDUCAÇÃO FISICA",
    "INICIAÇÃO CIENTÍFICA", "INICIAÇÃO CIENTIFICA",
    "PROJETO DE VIDA",
    "HISTÓRIA DA BAHIA IND AFR", "HISTORIA DA BAHIA CUL IND",
    "EDUCAÇÃO DIG E MIDIATICA", "EDUCAÇÃO DE DIG E MIDIATICA",
    "ESTAÇÃO APROF DE SABERES", "ESTAÇÃO DE APROF SABERES",
    "PROJETO TEC SOCIAIS EMPRE", "PROJ TECNOLOG SOCIAS EMP", "PROJETOS TEC SOCIAIS EMPRE",
    "MUNDO TRAB EMP INT SOCIAL", "EMPREENDEDORISMO INT SOCI", "MUND DO TRAB E REL INTERP",
    "FUND A INOVAÇ TECNOLOGICA", "FUND A INOV TECN",
    "HIGIENE SAÚDE E SEG TRAB", "HIGIENE SAÚDE SEG TRABALH", "HIGIENE SAÚDE E SED TRAB", "HIGIENE SAUDE E SEG TRAB", "HIGIENE OCUPACIONAL",
    "PRAT PROF INTER SOCIOCULT", "PRAT PROF INT SOCIOCULT",
}

# ======================================================================
# 2. MAPA DE MATÉRIAS TÉCNICAS POR CURSO
# Chave = Nome EXATO do Curso no banco (do seed_turmas.py)
# Valor = Lista de matérias técnicas normalizadas
# ======================================================================
MATERIAS_TECNICAS_POR_CURSO = {
    "Administração": [
        "ADM DO", "ADM FI", "ADM ME", "ADM MERC (MARK E NEG)", "MARKETING E NEGOCIAÇÃO",
        "ADMINISTRAÇÃO 3 SETOR", "ADMNISTRAÇÃO GERAL", "GESTAO",
        "CONTAB", "CONTA GERAL, GER E DE CUST", "CONT GERAL, GEREN E CUSTO",
        "DIREIT", "NOÇÕES DE DIREITO ADMINIS", "LEGISLAÇÃO TRABAL E PREVI",
        "ECONOM", "FUDAMENTOS DA ADM", "GESTÃO DE IMP SOCIOAMBIEN",
        "GESTÃO DE OP LOGISTICAS", "GESTÃO DE PESSOAS", "GESTÃO DE PRODUTIVIDADE",
        "GESTÃO DE QUALIDADE", "LOGISTICA", "MET E TEC ADMINISTRATIVAS", "MÉT E TÉC ADMINISTRATIVAS",
        "PROJETO EXPERIMENTAL II", "SIST I", "SISTEMA DE INF GERENCIAIS",
    ],
    "Análises Clínicas": [
        "ANATOMOFISIOLOGIA", "ANATOFISIOLOGIA",
        "BIOQUI", "CITOHISTOLOGIA", "COLETA AMOS INTERP EXAMES", "COLETA E MANIP AMOS BIOL",
        "FUND E GEST LABORATORIAL", "FUNDAMENTOS LAB CLINICO",
        "GESTÃO E QUALID DO LAB", "HEMATOLOGIA CLINICA", "HEMATO",
        "IMUNOL", "IFORMA APLIC TRAB SAÚDE", "INFORM", "INFOR APLIC TRAB SAÚDE",
        "MICROB", "PARASITOLOGIA", "PRIMEIROS SOCORROS", "PROJETO EXPERIEMNTAL II", "URINÁLISE",
    ],
    "Biotecnologia": [
        "BIOSSEGURANÇA", "INTROD BIOQUIMICA", "INTROD BIOTECNOLOGIA",
        "INTROD BIOTEC BIOPROC IND", "QUIMICA ORG E INORG",
    ],
    "Finanças": [
        "ANALIS DEMONS FINANCEIRAS", "CONTA B",
        "FUND DE MATEM FINANCEIRA", "FUNDO DE MAT FINACEIRA",
        "HISTORICOS INT SISTEM FIN", "HISTORICO INT SISTEMA FINA",
        "MERCADO DE CAPITAIS", "NOÇÕES DE DIREITO",
    ],
    "Logística": [
        "E E M", "GESTÃO DE OP.", "GESTAO", "GESTÃO DE OP LOGISTICAS",
        "INTRODUÇÃO LOGISTICA", "MÉT E TÉC ADMINISTRATIVAS", "SIST I"
    ],
    "Segurança do Trabalho": [
        "ADM E GEST APLIC A SEG", "ADM AP", "ASPECT",
        "LEGISLAÇÃO E NORMA DE SEG", "ORG E", "PREVEN",
        "PSICOL", "SAUDE", "SAUDE DO TRAB E ERGONOMIA", "SEGURA",
        "TECN SEG INDUD OPERACIONA", "TEC DE", "PROJETO EXPERIMENTAL II"
    ],
    "Serviços Jurídicos": [
        "DIREITO CIVIL", "DIREITO CONSTITUCIONAL", "DIREITO DIGITAL",
        "DIRETO EMPRESARIA TRIBUT", "DIREITO PENAL", "DIREITO PROCES E CIVIL",
        "ELEM DIR TRAB PRAT TRAB", "INTRUDUÇÃO ESTUDO DIREITO",
        "PRAT PROC CIVIL PENAL", "PRATICA PROCE CIVIL PENAL",
        "PROJETO EXPERIMENTAL II",
        "RH POST PROF QUALID ATEND", "RH, POSTURA PROF E QU.ATE",
        "SIST INF PARA AREA JURIDI", "SISTEMA INF AREA JURDICA",
        "TÉC ATEND PROCE E PRO ADM", "TEC ATEND PRROC PROCED ADM",
        "TEORIA GERAL DO PROCESSO",
    ],
    "Edificações": [
        "TOPOGRAFIA",
    ],
    "Enfermagem": [
        "POPULAÇÃO VULNERÁVEL", "PROCESSO SAÚDE-DOENÇA", "SAUDE PUBLICA INTEG II",
    ],
    "Panificação": [
        # Nenhuma matéria técnica foi encontrada no matérias.txt para este curso.
    ],
}


class Command(BaseCommand):
    help = "Popula a tabela 'GradeMateria' associando Cursos e Matérias (Base vs Técnica)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🚀 Iniciando o seed da Grade Curricular (Curso <-> Matéria)..."))

        # Contadores
        total_criados_base = 0
        total_criados_tecnica = 0
        total_erros_materia = 0

        # Iterar sobre cada Curso que existe no banco de dados
        for curso in Curso.objects.all():
            self.stdout.write(self.style.HTTP_INFO(f"\nProcessing Curso: {curso.nome}"))
            criados_base_curso = 0
            criados_tecnica_curso = 0

            # --- 1. Associar Matérias da BASE COMUM ---
            # Todos os cursos recebem a base comum
            for nome_materia_base in MATERIAS_BASE_COMUM:
                try:
                    materia_obj = Materia.objects.get(nome=nome_materia_base)
                    
                    # Usamos get_or_create para não duplicar
                    _, criado = GradeMateria.objects.get_or_create(
                        curso=curso, 
                        materia=materia_obj, 
                        defaults={'tipo': 'BASE'}
                    )
                    if criado:
                        criados_base_curso += 1
                
                except Materia.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  - [BASE] Matéria '{nome_materia_base}' não encontrada no banco. Foi pulada."))
                    total_erros_materia += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  - [BASE] Erro inesperado ao processar '{nome_materia_base}': {e}"))

            # --- 2. Associar Matérias TÉCNICAS ---
            # Pegamos a lista técnica específica para este curso
            lista_materias_tecnicas = MATERIAS_TECNICAS_POR_CURSO.get(curso.nome, [])
            
            if not lista_materias_tecnicas:
                self.stdout.write(f"  - Nenhuma matéria técnica específica definida para este curso.")
            
            for nome_materia_tecnica in lista_materias_tecnicas:
                try:
                    materia_obj = Materia.objects.get(nome=nome_materia_tecnica)
                    
                    _, criado = GradeMateria.objects.get_or_create(
                        curso=curso, 
                        materia=materia_obj, 
                        defaults={'tipo': 'TECNICA'}
                    )
                    if criado:
                        criados_tecnica_curso += 1
                
                except Materia.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  - [TECNICA] Matéria '{nome_materia_tecnica}' não encontrada no banco. Foi pulada."))
                    total_erros_materia += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  - [TECNICA] Erro inesperado ao processar '{nome_materia_tecnica}': {e}"))

            self.stdout.write(self.style.SUCCESS(f"  - {criados_base_curso} novas associações de Base Comum criadas."))
            self.stdout.write(self.style.SUCCESS(f"  - {criados_tecnica_curso} novas associações Técnicas criadas."))
            
            total_criados_base += criados_base_curso
            total_criados_tecnica += criados_tecnica_curso

        # --- FIM ---
        self.stdout.write(self.style.NOTICE(f"\n✅ Seed da Grade finalizado!"))
        self.stdout.write(f"   - Total de associações 'Base Comum' criadas: {total_criados_base}")
        self.stdout.write(f"   - Total de associações 'Técnicas' criadas: {total_criados_tecnica}")
        if total_erros_materia > 0:
            self.stdout.write(self.style.WARNING(f"   - Atenção: {total_erros_materia} matérias não foram encontradas no banco. Verifique o log acima."))