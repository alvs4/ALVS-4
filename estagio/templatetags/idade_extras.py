from django import template
from datetime import date

register = template.Library()

@register.filter
def is_menor(nascimento):
    if not nascimento:
        return False
    hoje = date.today()
    idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
    return idade < 18