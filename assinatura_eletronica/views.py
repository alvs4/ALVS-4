from django.shortcuts import render
import datetime
from core.models import DocumentoEstagio


# === QR CODE ===

def verificar_documento_publico(request, codigo_uuid):
    try:
        documento = DocumentoEstagio.objects.get(codigo_verificador=codigo_uuid)
    except DocumentoEstagio.DoesNotExist:
        return render(request, 'erro_verificacao.html', {
            'mensagem_erro': 'O código verificador não foi encontrado.'
        })

    estagio = documento.estagio
    aluno = estagio.aluno
    dados = documento.dados_formulario or {}
    
    for campo in ['data_inicio', 'data_fim']:
        valor = dados.get(campo)
        if isinstance(valor, str):
            try:
                dados[campo] = datetime.date.fromisoformat(valor)
            except ValueError:
                pass

    template_name = 'aluno/estagio/docs/TERMO-DE-COMPROMISSO_VISUALIZAR.html'
    
    context = {
        'documento': documento,
        'estagio': estagio,
        'aluno': aluno,
        'dados': dados,
        'pdf_existe': documento.pdf_supervisor_assinado.storage.exists(documento.pdf_supervisor_assinado.name) if documento.pdf_supervisor_assinado else False,
        'is_public_verification': True, 
    }
    
    return render(request, template_name, context)