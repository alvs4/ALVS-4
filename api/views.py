from django.http import JsonResponse
from core.models import Turma, Curso


# === VIEWS DE API ===

def get_opcoes_turma(request):
    curso_id = request.GET.get('curso_id')
    ano_modulo = request.GET.get('ano_modulo')
    turno = request.GET.get('turno')
    target = request.GET.get('target')

    queryset = Turma.objects.all()

    if curso_id: queryset = queryset.filter(curso_id=curso_id)
    if ano_modulo: queryset = queryset.filter(ano_modulo=ano_modulo)
    if turno: queryset = queryset.filter(turno=turno)

    if target == 'ano_modulo':
        data = list(queryset.order_by('ano_modulo').values_list('ano_modulo', flat=True).distinct())
        return JsonResponse({'options': data})

    if target == 'turno':
        turnos_existentes = list(queryset.values_list('turno', flat=True).distinct())
        data = []
        for valor, display in Turma.TURNO_CHOICES:
            if valor in turnos_existentes:
                data.append({'value': valor, 'display': display})
        return JsonResponse({'options': data})

    if target == 'turma':
        data = []
        for turma_obj in queryset.order_by('turma'):
            data.append({'id': turma_obj.id, 'display': turma_obj.nome_curto})
        return JsonResponse({'options': data})

    return JsonResponse({}, status=400)

def debug_log(request):
    print("\n===== DEBUG RECEBIDO DO FRONT =====")
    print("Curso:", request.GET.get('curso'))
    print("Ano/Módulo:", request.GET.get('ano_modulo'))
    print("Turno:", request.GET.get('turno'))
    print("Turma:", request.GET.get('turma'))
    print("===================================\n")
    return JsonResponse({'status': 'ok'})

def get_materias_por_curso(request):
    curso_id = request.GET.get('curso_id')
    if not curso_id:
        return JsonResponse({'materias': []})
    try:
        curso = Curso.objects.get(id=curso_id)
        materias = curso.materias.all().order_by('nome')
        
        materias_list = [{"id": materia.id, "nome": materia.nome} for materia in materias]
        
        return JsonResponse({'materias': materias_list})
        
    except Curso.DoesNotExist:
        return JsonResponse({'materias': []})