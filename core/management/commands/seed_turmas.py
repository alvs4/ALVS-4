# Em core/management/commands/seed_turmas.py

from django.core.management.base import BaseCommand
from core.models import Curso, Turma
from django.db import IntegrityError

class Command(BaseCommand):
    help = "Popula o banco com a estrutura completa de cursos e turmas do CEEP Guanambi."

    def handle(self, *args, **kwargs):
        cursos_dados = {
            # Eixo da Saúde
            "Análises Clínicas": {
                "eixo": "SAUDE", "turmas": [
                    ('1º ANO', 'matutino', 'M1', 'SALA 04'), ('1º ANO', 'vespertino', 'V1', 'SALA 03'),
                    ('2º ANO', 'matutino', 'M1', 'SALA 14'), ('2º ANO', 'vespertino', 'V1', 'SALA 13'), ('2º ANO', 'vespertino', 'V2', 'SALA 14'),
                    ('3º ANO', 'matutino', 'M1', 'SALA 04 PAV - A'), ('3º ANO', 'matutino', 'M2', 'SALA 02 PAV - A'),
                    ('3º ANO', 'vespertino', 'V1', 'SALA 04 PAV - A'), ('3º ANO', 'vespertino', 'V2', 'SALA 02 PAV - A'),
                    ('I MÓDULO', 'noturno', None, 'SALA 14', 'SUBSEQUENTE'), ('II MÓDULO', 'noturno', None, 'SALA 15', 'SUBSEQUENTE'),
                    ('III MÓDULO', 'noturno', None, 'SALA 16', 'SUBSEQUENTE'), ('IV MÓDULO', 'noturno', None, 'SALA 17', 'SUBSEQUENTE'),
                ]
            },
            "Enfermagem": {
                "eixo": "SAUDE", "turmas": [
                    ('III MÓDULO', 'noturno', None, 'SALA 18', 'SUBSEQUENTE'), ('IV MÓDULO', 'noturno', None, 'SALA 19', 'SUBSEQUENTE'),
                    ('V MÓDULO', 'noturno', None, 'SALA 23', 'SUBSEQUENTE'), ('VI MÓDULO', 'noturno', None, 'SALA 24', 'SUBSEQUENTE'),
                ]
            },
            "Segurança do Trabalho": {
                "eixo": "SAUDE", "turmas": [
                    ('1º ANO', 'matutino', 'M1', 'SALA 08'), ('1º ANO', 'vespertino', 'V1', 'SALA 08'),
                    ('2º ANO', 'matutino', 'M1', 'SALA 17'), ('2º ANO', 'vespertino', 'V1', 'SALA 17'),
                    ('3º ANO', 'matutino', 'M1', 'SALA 24'), ('3º ANO', 'vespertino', 'V1', 'SALA 24'),
                    ('II MÓDULO', 'noturno', None, 'SALA 21', 'SUBSEQUENTE'), ('III MÓDULO', 'noturno', None, 'SALA 22', 'SUBSEQUENTE'),
                ]
            },
            # Eixo de Gestão
            "Administração": {
                "eixo": "GESTAO", "turmas": [
                    ('1º ANO', 'matutino', 'M1', 'SALA 02'), ('1º ANO', 'matutino', 'M2', 'SALA 03'), ('1º ANO', 'vespertino', 'V1', 'SALA 02'),
                    ('2º ANO', 'matutino', 'M1', 'SALA 13'), ('2º ANO', 'vespertino', 'V1', 'SALA 10'),
                    ('3º ANO', 'matutino', 'M1', 'SALA 19'), ('3º ANO', 'matutino', 'M2', 'SALA 20'), ('3º ANO', 'matutino', 'M3', 'SALA 21'),
                    ('3º ANO', 'vespertino', 'V1', 'SALA 21'), ('3º ANO', 'vespertino', 'V2', 'SALA 22'),
                    ('II MÓDULO', 'noturno', None, 'SALA 02', 'PROEJA'), ('III MÓDULO', 'noturno', None, 'SALA 03', 'PROEJA'),
                    ('IV MÓDULO', 'noturno', None, 'SALA 04', 'PROEJA'), ('II MÓDULO', 'noturno', None, 'SALA 13', 'SUBSEQUENTE'),
                ]
            },
            "Biotecnologia": {
                "eixo": "GESTAO", "turmas": [
                    ('1º ANO', 'matutino', 'M1', 'SALA 05'), ('1º ANO', 'vespertino', 'V1', 'SALA 04'), ('1º ANO', 'vespertino', 'V2', 'SALA 05'),
                    ('2º ANO', 'matutino', 'M1', None),
                    ('3º ANO', 'vespertino', 'V1', 'SALA 19'),
                ]
            },
            "Finanças": {
                "eixo": "GESTAO", "turmas": [
                    ('1º ANO', 'matutino', 'M1', 'SALA 06'), ('1º ANO', 'vespertino', 'V1', 'SALA 06'),
                    ('2º ANO', 'matutino', 'M1', 'SALA 15'), ('2º ANO', 'vespertino', 'V1', 'SALA 15'),
                    ('3º ANO', 'matutino', 'M1', None),
                ]
            },
            "Logística": {
                "eixo": "GESTAO", "turmas": [
                    ('1º ANO', 'matutino', 'M1', 'SALA 07'), ('1º ANO', 'vespertino', 'V1', 'SALA 07'),
                    ('2º ANO', 'matutino', 'M1', 'SALA 16'), ('2º ANO', 'vespertino', 'V1', 'SALA 16'),
                    ('3º ANO', 'matutino', 'M1', None),
                    ('I MÓDULO', 'noturno', None, 'SALA 06', 'PROEJA'),
                ]
            },
            "Serviços Jurídicos": {
                "eixo": "GESTAO", "turmas": [
                    ('1º ANO', 'matutino', 'M1', 'SALA 09'), ('1º ANO', 'matutino', 'M2', 'SALA 10'), ('1º ANO', 'vespertino', 'V1', 'SALA 09'),
                    ('2º ANO', 'matutino', 'M1', 'SALA 18'), ('2º ANO', 'vespertino', 'V1', 'SALA 18'), ('2º ANO', 'vespertino', 'V2', 'SALA 20'),
                    ('3º ANO', 'matutino', 'M1', 'SALA 22'), ('3º ANO', 'matutino', 'M2', 'SALA 23'), ('3º ANO', 'vespertino', 'V1', 'SALA 23'),
                    ('II MÓDULO', 'noturno', None, 'SALA 07', 'PROEJA'), ('IV MÓDULO', 'noturno', None, 'SALA 08', 'PROEJA'), ('V MÓDULO', 'noturno', None, 'SALA 09', 'PROEJA'),
                ]
            },
            "Edificações": { "eixo": "GESTAO", "turmas": [('I MÓDULO', 'noturno', None, 'SALA 20', 'SUBSEQUENTE')] },
            "Panificação": { "eixo": "GESTAO", "turmas": [('I MÓDULO', 'noturno', None, 'SALA 05', 'PROEJA')] },
        }

        self.stdout.write(self.style.NOTICE("🚀 Iniciando o seed de cursos e turmas..."))
        
        cursos_criados, cursos_atualizados, turmas_criadas, turmas_atualizadas = 0, 0, 0, 0

        for nome_curso, dados_curso in cursos_dados.items():
            curso, criado = Curso.objects.update_or_create(nome=nome_curso, defaults={'eixo': dados_curso["eixo"]})
            if criado: cursos_criados += 1
            else: cursos_atualizados += 1
            
            for dados_turma in dados_curso["turmas"]:
                if len(dados_turma) == 5:
                    ano_modulo, turno, turma_nome, sala, modalidade = dados_turma
                else:
                    ano_modulo, turno, turma_nome, sala = dados_turma
                    modalidade = None
                
                try:
                    _, criado = Turma.objects.update_or_create(
                        curso=curso, ano_modulo=ano_modulo, turno=turno,
                        turma=turma_nome, modalidade=modalidade,
                        defaults={'sala': sala} 
                    )
                    if criado: turmas_criadas += 1
                    else: turmas_atualizadas += 1
                except IntegrityError as e:
                    self.stdout.write(self.style.WARNING(f"⚠️ Erro de integridade ao processar {curso}-{ano_modulo}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"✅ Seed finalizado!"))
        self.stdout.write(f"   - Cursos criados: {cursos_criados}")
        self.stdout.write(f"   - Cursos atualizados: {cursos_atualizados}")
        self.stdout.write(f"   - Turmas criadas: {turmas_criadas}")
        self.stdout.write(f"   - Turmas atualizadas: {turmas_atualizadas}")