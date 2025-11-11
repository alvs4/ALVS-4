from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils.timezone import now
from core.models import Turma, ProfessorMateriaAnoCursoModalidade
from core.decorators import role_required
from .forms import EmailAuthenticationForm


# === AUTENTICAÇÃO ===

@login_required
def redirect_por_tipo(request):
    if request.user.tipo == 'admin':
        return redirect('admin_dashboard')
    elif request.user.tipo == 'professor':
        return redirect('professor_dashboard')
    elif request.user.tipo == 'aluno':
        return redirect('aluno_dashboard')
    elif request.user.tipo == 'servidor' or request.user.tipo == 'direcao':
        return redirect('servidor_dashboard')
    return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect_por_tipo(request)
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                messages.success(
                    request, f"Bem-vindo(a), {user.first_name or user.email}")
                if user.tipo == 'admin':
                    return redirect('admin_dashboard')
                elif user.tipo == 'professor':
                    return redirect('professor_dashboard')
                elif user.tipo == 'aluno':
                    return redirect('aluno_dashboard')
                elif user.tipo == 'servidor' or user.tipo == 'direcao':
                    return redirect('servidor_dashboard')
                    
                messages.warning(request, "Tipo de usuário não reconhecido.")
                return redirect('login')
            else:
                messages.error(request, "Email ou senha inválidos.")
        else:
            messages.error(request, "Email ou senha inválidos.")
    else:
        form = EmailAuthenticationForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Você foi desconectado(a).")
    return redirect('login')


@login_required
def ver_perfil(request):
    user = request.user
    turmas = []
    vinculos = []

    if user.tipo == 'aluno':
        turmas = Turma.objects.filter(alunoturma__aluno=user)

    elif user.tipo == 'professor':
        vinculos = ProfessorMateriaAnoCursoModalidade.objects.filter(professor=user).select_related('materia', 'curso')

    return render(request, 'perfil/ver_perfil.html', {
        'user': user,
        'turmas': turmas,
        'vinculos': vinculos
    })

@login_required
@role_required('professor', 'aluno', 'servidor', 'direcao') 
def alterar_senha(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            
            print(f"[LOG] Senha alterada por: {user.username} em {now()}")
            user.senha_temporaria = False
            user.save()
            
            update_session_auth_hash(request, user)
            messages.success(request, "Senha atualizada com sucesso.")
            return redirect('ver_perfil') 
        else:
            messages.error(request, "Corrija os erros abaixo.")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'perfil/alterar_senha.html', {'form': form})