# Em core/management/commands/seed_materias_completo.py

from django.core.management.base import BaseCommand
from core.models import Materia
import sys

class Command(BaseCommand):
    help = "Popula o banco de dados com a lista COMPLETA de matérias (Base Comum + Técnicas) do CEEP, baseada no matérias.txt"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🚀 Iniciando o seed COMPLETO de matérias..."))

        # 1. LISTA DA BASE COMUM (EIXOS GERAIS)
        # Inclui variações encontradas no .txt (ex: "LP E R", "HISTORIA")
        materias_base_comum = [
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
            "HISTÓRIA DA BAHIA IND AFR", "HISTORIA DA BAHIA CUL IND", "HISTORIA DA BAHIA IND AFR",
            "EDUCAÇÃO DIG E MIDIATICA", "EDUCAÇÃO DE DIG E MIDIATICA",
            "ESTAÇÃO APROF DE SABERES", "ESTAÇÃO DE APROF SABERES",
            "PROJETO TEC SOCIAIS EMPRE", "PROJ TECNOLOG SOCIAS EMP", "PROJETOS TEC SOCIAIS EMPRE",
            "MUNDO TRAB EMP INT SOCIAL", "EMPREENDEDORISMO INT SOCI", "MUND DO TRAB E REL INTERP",
            "FUND A INOVAÇ TECNOLOGICA", "FUND A INOV TECN",
            "HIGIENE SAÚDE E SEG TRAB", "HIGIENE SAÚDE SEG TRABALH", "HIGIENE SAÚDE E SED TRAB", "HIGIENE SAUDE E SEG TRAB", "HIGIENE OCUPACIONAL",
            "PRAT PROF INTER SOCIOCULT", "PRAT PROF INT SOCIOCULT",
        ]

        # 2. LISTA DAS MATÉRIAS TÉCNICAS (POR CURSO)
        # Baseado na análise do matérias.txt
        materias_tecnicas = [
            # ADMINISTRAÇÃO
            "ADM DO", "ADM FI", "ADM ME", "ADM MERC (MARK E NEG)", "MARKETING E NEGOCIAÇÃO",
            "ADMINISTRAÇÃO 3 SETOR", "ADMNISTRAÇÃO GERAL", "GESTAO",
            "CONTAB", "CONTA GERAL, GER E DE CUST", "CONT GERAL, GEREN E CUSTO",
            "DIREIT", "NOÇÕES DE DIREITO ADMINIS", "LEGISLAÇÃO TRABAL E PREVI",
            "ECONOM", "FUDAMENTOS DA ADM", "GESTÃO DE IMP SOCIOAMBIEN",
            "GESTÃO DE OP LOGISTICAS", "GESTÃO DE PESSOAS", "GESTÃO DE PRODUTIVIDADE",
            "GESTÃO DE QUALIDADE", "LOGISTICA", "MET E TEC ADMINISTRATIVAS", "MÉT E TÉC ADMINISTRATIVAS",
            "PROJETO EXPERIMENTAL II", "SIST I", "SISTEMA DE INF GERENCIAIS",

            # ANÁLISES CLÍNICAS
            "ANATOMOFISIOLOGIA", "ANATOFISIOLOGIA",
            "BIOQUI", "CITOHISTOLOGIA", "COLETA AMOS INTERP EXAMES", "COLETA E MANIP AMOS BIOL",
            "FUND E GEST LABORATORIAL", "FUNDAMENTOS LAB CLINICO",
            "GESTÃO E QUALID DO LAB", "HEMATOLOGIA CLINICA", "HEMATO",
            "IMUNOL", "IFORMA APLIC TRAB SAÚDE", "INFORM", "INFOR APLIC TRAB SAÚDE",
            "MICROB", "PARASITOLOGIA", "PRIMEIROS SOCORROS", "PROJETO EXPERIEMNTAL II", "URINÁLISE",

            # BIOTECNOLOGIA
            "BIOSSEGURANÇA", "INTROD BIOQUIMICA", "INTROD BIOTECNOLOGIA",
            "INTROD BIOTEC BIOPROC IND", "QUIMICA ORG E INORG",

            # FINANÇAS
            "ANALIS DEMONS FINANCEIRAS", "CONTA B",
            "FUND DE MATEM FINANCEIRA", "FUNDO DE MAT FINACEIRA",
            "HISTORICOS INT SISTEM FIN", "HISTORICO INT SISTEMA FINA",
            "MERCADO DE CAPITAIS", "NOÇÕES DE DIREITO",

            # LOGÍSTICA
            "E E M", "GESTÃO DE OP.",
            "INTRODUÇÃO LOGISTICA",

            # SEGURANÇA DO TRABALHO
            "ADM E GEST APLIC A SEG", "ADM AP", "ASPECT",
            "LEGISLAÇÃO E NORMA DE SEG", "ORG E", "PREVEN",
            "PSICOL", "SAUDE", "SAUDE DO TRAB E ERGONOMIA", "SEGURA",
            "TECN SEG INDUD OPERACIONA", "TEC DE",

            # SERVIÇOS JURÍDICOS
            "DIREITO CIVIL", "DIREITO CONSTITUCIONAL", "DIREITO DIGITAL",
            "DIRETO EMPRESARIA TRIBUT", "DIREITO PENAL", "DIREITO PROCES E CIVIL",
            "ELEM DIR TRAB PRAT TRAB", "INTRUDUÇÃO ESTUDO DIREITO",
            "PRAT PROC CIVIL PENAL", "PRATICA PROCE CIVIL PENAL",
            "RH POST PROF QUALID ATEND", "RH, POSTURA PROF E QU.ATE",
            "SIST INF PARA AREA JURIDI", "SISTEMA INF AREA JURDICA",
            "TÉC ATEND PROCE E PRO ADM", "TEC ATEND PRROC PROCED ADM",
            "TEORIA GERAL DO PROCESSO",

            # EDIFICAÇÕES
            "TOPOGRAFIA",

            # ENFERMAGEM
            "POPULAÇÃO VULNERÁVEL", "PROCESSO SAÚDE-DOENÇA", "SAUDE PUBLICA INTEG II",
        ]

        # 3. COMBINAR E LIMPAR AS LISTAS
        todas_as_materias_lista = materias_base_comum + materias_tecnicas

        # Usamos um 'set' para garantir que cada nome de matéria seja único
        materias_unicas = set()
        for nome in todas_as_materias_lista:
            try:
                # .strip() remove espaços em branco no início e no fim
                # .upper() converte tudo para maiúsculas para padronização
                nome_normalizado = nome.strip().upper() 
                
                if nome_normalizado: # Garante que não é uma string vazia
                    materias_unicas.add(nome_normalizado)
            except AttributeError:
                self.stdout.write(self.style.WARNING(f"⚠️ Aviso: Ignorando item inválido '{nome}'."))
                continue

        materias_criadas = 0
        materias_existentes = 0

        # 4. EXECUTAR O SEED
        # Ordenamos a lista para que o log de saída seja alfabético
        for nome_materia in sorted(list(materias_unicas)):
            # get_or_create:
            # 1. Tenta encontrar uma Materia com 'nome=nome_materia'.
            # 2. Se encontrar, 'obj' será a matéria e 'criado' será False.
            # 3. Se NÃO encontrar, cria uma nova, 'obj' será a nova matéria e 'criado' será True.
            obj, criado = Materia.objects.get_or_create(nome=nome_materia)

            if criado:
                materias_criadas += 1
                self.stdout.write(f"   - Matéria '{obj.nome}' criada.")
            else:
                materias_existentes += 1
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Seed COMPLETO finalizado!"))
        self.stdout.write(f"   - Novas matérias criadas: {materias_criadas}")
        self.stdout.write(f"   - Matérias que já existiam: {materias_existentes}")