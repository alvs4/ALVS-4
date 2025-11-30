from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    # AUTENTICACAO
    path('', views.redirect_por_tipo, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verificar-2fa/', views.verificar_2fa, name='verificar_2fa'),
    path('reenviar-codigo/', views.reenviar_codigo, name='reenviar_codigo'),
    path("configurar-autenticador/", views.configurar_google_authenticator, name="configurar_autenticador"),
    path("desativar-autenticador/", views.desativar_google_authenticator, name="desativar_google_authenticator"),
    path("recuperar-senha/", views.recuperar_senha, name="recuperar_senha"),
    path("redefinir-senha/<str:token>/", views.redefinir_senha, name="redefinir_senha"),
    path("escolher-metodo-2fa/", views.escolher_metodo_2fa, name="escolher_metodo_2fa"),
    path("verificar-totp/", views.verificar_totp, name="verificar_totp"),

    # PERFIL
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('perfil/alterar_senha/', views.alterar_senha, name='alterar_senha'),
    path("perfil/inserir-email/", views.inserir_email, name="inserir_email"),
    path("confirmar-email/<str:token>/", views.confirmar_email, name="confirmar_email"),
]