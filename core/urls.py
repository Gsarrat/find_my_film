from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # Login 
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('register/', views.register, name='register'),

    # Persona e recomendacoes
    path('persona/', views.persona_view, name='persona'),
    path('recomendacoes/<str:titulo>/assistido/', views.marcar_assistido, name='marcar_assistido'),

    # Painel do usuario
    path('meu-perfil/', views.dashboard_view, name='dashboard'),
]
