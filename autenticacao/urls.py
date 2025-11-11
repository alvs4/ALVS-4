from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required


urlpatterns = [
    # AUTENTICACAO
    path('', views.redirect_por_tipo, name='inicio'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # PERFIL
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('perfil/alterar_senha/', views.alterar_senha, name='alterar_senha'),
]