from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.utils.timezone import now
from django.urls import reverse
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.http import HttpResponse
from datetime import timedelta
from core.models import CustomUser, Turma, ProfessorMateriaAnoCursoModalidade
from core.decorators import role_required
from .forms import EmailAuthenticationForm, InserirEmailForm, Codigo2FAForm
import uuid, random, pyotp, qrcode, io, base64


# === AUTENTICAÇÃO ===

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

                # === ADMIN NÃO USA 2FA ===
                if user.tipo == "admin":
                    login(request, user)
                    return redirect_por_tipo(request)

                user.backend = "django.contrib.auth.backends.ModelBackend"
                token_cookie = request.COOKIES.get("trusted_device")

                # Verifica dispositivo confiável
                if token_cookie:
                    if (
                        user.lembrar_dispositivo_token == token_cookie and
                        user.lembrar_dispositivo_expira > now()
                    ):
                        login(request, user, backend=user.backend)
                        return redirect_por_tipo(request)

                # VERIFICA SE TOTP ESTÁ ATIVO
                tem_totp = user.usa_google_authenticator and user.secret_2fa

                # VERIFICA SE 2FA POR E-MAIL ESTÁ ATIVO
                tem_email_2fa = (
                    user.email 
                    and user.email.strip() != "" 
                    and user.email_confirmado
                )

                # Guarda o ID do usuário na sessão
                request.session["usuario_2fa"] = user.id

                # Se tiver ambos → escolher método
                if tem_totp and tem_email_2fa:
                    return redirect("escolher_metodo_2fa")

                # Se tiver APENAS TOTP
                if tem_totp:
                    return redirect("verificar_totp")

                # Se tiver APENAS EMAIL 2FA
                if tem_email_2fa:
                    codigo = f"{random.randint(100000, 999999)}"
                    user.codigo_2fa = codigo
                    user.codigo_2fa_expira = now() + timedelta(minutes=5)
                    user.tentativas_2fa = 0
                    user.save()

                    if not user.email:
                        messages.error(request, "Seu usuário não possui e-mail cadastrado. Não é possível usar 2FA por e-mail.")
                        return redirect("inserir_email")
                    
                    # Envia email HTML
                    html_content = render_to_string(
                        "email/codigo_2fa.html",
                        {"codigo": codigo}
                    )

                    msg = EmailMultiAlternatives(
                        "Seu código de segurança",
                        "",
                        f"ALVS-4 <{settings.DEFAULT_FROM_EMAIL}>",
                        [user.email],
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send()

                    return redirect("verificar_2fa")

                # Nenhum método ativo (falha de configuração)
                login(request, user)
                return redirect_por_tipo(request)

            else:
                messages.error(request, "Email ou senha inválidos.")

    else:
        form = EmailAuthenticationForm()

    return render(request, "login.html", {"form": form})

def verificar_totp(request):
    user_id = request.session.get("usuario_2fa")
    if not user_id:
        return redirect("login")

    user = CustomUser.objects.get(id=user_id)

    if not user.usa_google_authenticator:
        messages.error(request, "Google Authenticator não está ativado.")
        return redirect("login")

    totp = pyotp.TOTP(user.secret_2fa)

    if request.method == "POST":
        codigo = request.POST.get("codigo")

        if totp.verify(codigo):
            user.backend = "django.contrib.auth.backends.ModelBackend"
            login(request, user)
            return redirect_por_tipo(request)
        else:
            messages.error(request, "Código inválido.")

    return render(request, "autenticacao/verificar_totp.html")

def verificar_2fa(request):
    user_id = request.session.get("usuario_2fa")
    if not user_id:
        return redirect("login")

    user = CustomUser.objects.get(id=user_id)

    if request.method == "POST":
        form = Codigo2FAForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data["codigo"]

            if user.tentativas_2fa >= 5:
                messages.error(request, "Muitas tentativas. Aguarde 10 minutos.")
                return redirect("login")

            if codigo == user.codigo_2fa and user.codigo_2fa_expira > now():
                user.backend = "autenticacao.backends.CustomBackend"
                login(request, user)

                if "lembrar_dispositivo" in request.POST:
                    token = uuid.uuid4().hex
                    user.lembrar_dispositivo_token = token
                    user.lembrar_dispositivo_expira = now() + timedelta(days=30)
                    user.save()

                    response = redirect_por_tipo(request)
                    response.set_cookie("trusted_device", token, max_age=30*24*3600)
                    return response

                return redirect_por_tipo(request)

            user.tentativas_2fa += 1
            user.save()
            messages.error(request, "Código incorreto.")

    else:
        form = Codigo2FAForm()

    return render(request, "autenticacao/verificar_2fa.html", {"form": form})

def escolher_metodo_2fa(request):
    user_id = request.session.get("usuario_2fa")
    if not user_id:
        return redirect("login")

    user = CustomUser.objects.get(id=user_id)

    usa_totp = user.usa_google_authenticator and user.secret_2fa

    usa_email = (
        user.dois_fatores_email and
        user.email and
        user.email.strip() != "" and
        user.email_confirmado
    )
    
    print("DEBUG 2FA EMAIL:")
    print("email:", user.email)
    print("email_confirmado:", user.email_confirmado)
    print("dois_fatores_email:", user.dois_fatores_email)
    print("USA EMAIL 2FA:", usa_email)

    return render(request, "autenticacao/escolher_metodo_2fa.html", {
        "usa_totp": usa_totp,
        "usa_email": usa_email,
    })

def reenviar_codigo(request):
    user_id = request.session.get("usuario_2fa")
    if not user_id:
        return redirect("login")

    user = CustomUser.objects.get(id=user_id)

    codigo = f"{random.randint(100000, 999999)}"
    user.codigo_2fa = codigo
    user.codigo_2fa_expira = now() + timedelta(minutes=5)
    user.save()

    if not user.email:
        messages.error(request, "Seu usuário não possui e-mail cadastrado. Não é possível usar 2FA por e-mail.")
        return redirect("inserir_email")
    
    html_content = render_to_string(
        "email/novo_codigo_2fa.html",
        {"codigo": codigo}
    )

    subject = "Novo Código de Segurança"
    from_email = f"ALVS-4 <{settings.DEFAULT_FROM_EMAIL}>"
    to = [user.email]

    msg = EmailMultiAlternatives(subject, "", from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

    messages.success(request, "Código reenviado!")
    return redirect("verificar_2fa")

@login_required
def configurar_google_authenticator(request):
    user = request.user

    # 🔹 Reconfigurar
    if request.GET.get("reconfigurar") == "1":
        user.secret_2fa = pyotp.random_base32()
        user.usa_google_authenticator = False
        user.save()

    # 🔹 Criar secret novo se não existir
    if not user.secret_2fa:
        user.secret_2fa = pyotp.random_base32()
        user.save()

    secret = user.secret_2fa
    totp = pyotp.TOTP(secret)
    
    nome_seguro = f"{user.id}"
    if user.email:
        nome_seguro = user.email.replace("@", "_").replace(".", "_") + f"-{user.id}"

    provisioning_url = totp.provisioning_uri(
        name=nome_seguro,
        issuer_name="ALVS4"
    )

    print("PROVISIONING URL:", provisioning_url)

    # 🔹 Gerar QR Code
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=4,
    )
    qr.add_data(provisioning_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # 🔹 Validar código do Authenticator
    if request.method == "POST":
        codigo = request.POST.get("codigo")

        if totp.verify(codigo):
            user.usa_google_authenticator = True
            user.save()
            messages.success(request, "Google Authenticator configurado com sucesso!")
            return redirect("ver_perfil")
        else:
            messages.error(request, "Código inválido! Tente novamente.")

    return render(request, "autenticacao/configurar_autenticator.html", {
        "qr_code_url": f"data:image/png;base64,{qr_base64}"
    })

    
@login_required
def desativar_google_authenticator(request):
    user = request.user

    # Se o usuário não usa Google Authenticator, redireciona
    if not user.usa_google_authenticator:
        messages.info(request, "Você não possui o Google Authenticator ativado.")
        return redirect("configurar_google_authenticator")

    if request.method == "POST":
        user.usa_google_authenticator = False
        user.save()
        messages.success(request, "Google Authenticator desativado com sucesso!")
        return redirect("ver_perfil")

    return render(request, "autenticacao/desativar_autenticator.html")

def recuperar_senha(request):
    if request.method == "POST":
        identificador = request.POST.get("identificador").strip()

        try:
            user = CustomUser.objects.get(username=identificador)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(email=identificador)
            except CustomUser.DoesNotExist:
                messages.error(request, "Nenhum usuário encontrado com essa matrícula ou e-mail.")
                return redirect("recuperar_senha")

        token = uuid.uuid4().hex
        user.token_recuperacao_senha = token
        user.save()

        link = request.build_absolute_uri(
            reverse("redefinir_senha", args=[token])
        )

        html_email = f"""
        <html>
        <body style="font-family: Arial; background:#f4f4f4; padding:25px;">
            <div style="max-width:520px; margin:auto; background:white; padding:25px;
                        border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,.15);">
                
                <h2 style="color:#333; text-align:center;">Redefinição de Senha</h2>

                <p>Olá, {user.first_name or user.username}!</p>

                <p>Você solicitou a redefinição de senha para sua conta do sistema <b>ALVS-4</b>.</p>

                <div style="margin:25px 0; text-align:center;">
                    <a href="{link}" style="
                        padding:12px 25px;
                        background:#1a73e8;
                        color:white;
                        text-decoration:none;
                        border-radius:6px;
                        font-size:16px;">
                        Redefinir Senha
                    </a>
                </div>

                <p>Se o botão não funcionar, copie e cole o link abaixo:</p>
                <p style="word-break: break-all; color:#1a73e8;">{link}</p>

                <hr>
                <p style="font-size:12px; text-align:center; color:#777;">
                    ALVS-4 — Sistema de Gestão<br>
                    Mensagem automática — não responda.
                </p>
            </div>
        </body>
        </html>
        """

        msg = EmailMultiAlternatives(
            "Redefinição de Senha",
            "",
            f"ALVS-4 <{settings.DEFAULT_FROM_EMAIL}>",
            [user.email],
        )
        msg.attach_alternative(html_email, "text/html")
        if not user.email:
            messages.error(request, "Seu usuário não possui e-mail cadastrado. Não é possível usar 2FA por e-mail.")
            return redirect("inserir_email")
        msg.send()

        messages.success(request, "Se existir uma conta, enviaremos um link para redefinir a senha.")
        return redirect("login")

    return render(request, "autenticacao/recuperar_senha.html")

def redefinir_senha(request, token):
    try:
        user = CustomUser.objects.get(token_recuperacao_senha=token)
    except CustomUser.DoesNotExist:
        messages.error(request, "Token inválido ou expirado.")
        return redirect("login")

    if request.method == "POST":
        senha1 = request.POST.get("senha1")
        senha2 = request.POST.get("senha2")

        if senha1 != senha2:
            messages.error(request, "As senhas não coincidem.")
            return redirect(request.path)

        user.set_password(senha1)
        user.token_recuperacao_senha = None
        user.save()

        messages.success(request, "Senha redefinida com sucesso! Faça login.")
        return redirect("login")

    return render(request, "autenticacao/redefinir_senha.html")

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
def inserir_email(request):
    user = request.user

    if request.method == "POST":
        form = InserirEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]

            token = uuid.uuid4().hex
            user.email = email
            user.token_confirmacao_email = token
            user.email_confirmado = False
            user.save()

            link = request.build_absolute_uri(
                reverse("confirmar_email", args=[token])
            )

            if not user.email:
                messages.error(request, "Seu usuário não possui e-mail cadastrado. Não é possível usar 2FA por e-mail.")
                return redirect("inserir_email")
            
            html_content = render_to_string(
                "email/confirmar_email.html",
                {"link": link}
            )

            subject = "Confirme seu e-mail"
            from_email = f"ALVS-4 <{settings.DEFAULT_FROM_EMAIL}>"
            to = [email]

            msg = EmailMultiAlternatives(subject, "", from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            messages.success(request, "E-mail enviado! Verifique sua caixa de entrada.")
            return redirect("ver_perfil")
    else:
        form = InserirEmailForm()

    return render(request, "perfil/inserir_email.html", {"form": form})


@login_required
@role_required('professor', 'aluno', 'servidor', 'direcao')
def confirmar_email(request, token):
    try:
        user = CustomUser.objects.get(token_confirmacao_email=token)
    except CustomUser.DoesNotExist:
        messages.error(request, "Token inválido ou expirado.")
        return redirect("ver_perfil")

    user.email_confirmado = True
    user.dois_fatores_email = True
    user.token_confirmacao_email = None
    user.save()

    messages.success(request, "E-mail confirmado com sucesso!")
    return redirect("ver_perfil")

@login_required
@role_required('professor', 'aluno', 'servidor', 'direcao')
def alterar_senha(request):
    if not request.user.email:
        messages.error(request, "Você precisa adicionar um e-mail antes de alterar a senha.")
        return redirect('inserir_email')

    if not request.user.email_confirmado:
        messages.error(request, "Confirme seu e-mail antes de alterar a senha.")
        return redirect('inserir_email')

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