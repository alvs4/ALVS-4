from django.core.management.base import BaseCommand
from core.models import Curso, Turma
from django.db import IntegrityError

class Command(BaseCommand):
    help = "Cria todas as turmas (1º ao 3º ANO e I ao VI MÓDULO) para todos os cursos."

    def handle(self, *args, **kwargs):

        self.stdout.write(self.style.NOTICE("\n🚀 Iniciando seed automático de turmas...\n"))

        # Turnos regulares
        turnos_regulares = {
            "matutino": ["M1", "M2"],
            "vespertino": ["V1", "V2"]
        }

        # Módulos noturnos (PROEJA e SUBSEQUENTE)
        modalidades_noturno = ["PROEJA", "SUBSEQUENTE"]

        anos = ["1º ANO", "2º ANO", "3º ANO"]
        modulos = ["I MÓDULO", "II MÓDULO", "III MÓDULO", "IV MÓDULO", "V MÓDULO", "VI MÓDULO"]

        cursos = Curso.objects.all()

        turmas_criadas = 0
        turmas_atualizadas = 0

        for curso in cursos:

            # --------------------------------------
            # Criando ANOS (matutino e vespertino)
            # --------------------------------------
            for ano in anos:
                for turno, codigos in turnos_regulares.items():
                    for codigo in codigos:

                        obj, created = Turma.objects.update_or_create(
                            curso=curso,
                            ano_modulo=ano,
                            turno=turno,
                            turma=codigo,
                            modalidade="EPI",  # sempre EPI no matutino/vespertino
                            defaults={"sala": None}
                        )

                        if created:
                            turmas_criadas += 1
                        else:
                            turmas_atualizadas += 1

            # --------------------------------------
            # Criando MÓDULOS (noturno)
            # --------------------------------------
            for modulo in modulos:
                for modalidade in modalidades_noturno:

                    obj, created = Turma.objects.update_or_create(
                        curso=curso,
                        ano_modulo=modulo,
                        turno="noturno",
                        turma=None,  # módulos não têm M1/M2/V1/V2
                        modalidade=modalidade,
                        defaults={"sala": None}
                    )

                    if created:
                        turmas_criadas += 1
                    else:
                        turmas_atualizadas += 1

        # FIM
        self.stdout.write(self.style.SUCCESS("\n✅ Seed finalizado com sucesso!"))
        self.stdout.write(f"   → Turmas criadas: {turmas_criadas}")
        self.stdout.write(f"   → Turmas atualizadas: {turmas_atualizadas}\n")
