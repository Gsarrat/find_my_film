from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView

from .models import Post
from .forms import PersonaForm
from .recommender import gerar_recomendacoes



class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        messages.success(self.request, 'Você está logado!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Usuário ou senha inválidos. Tente novamente.')
        return super().form_invalid(form)
    



def index(request):
    posts = Post.objects.all().order_by('-criado_em')
    return render(request, 'index.html', {'posts': posts})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Conta criada com sucesso para {username}!')
            login(request, user)  # Faz login automático após cadastro
            return redirect('index')
        else:
            messages.error(request, 'Erro ao criar conta. Verifique os campos.')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def persona_view(request):
    if request.method == 'POST':
        form = PersonaForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data
            recomendacoes_html = gerar_recomendacoes(dados)
            return render(request, 'recomendacoes.html', {'recomendacoes': recomendacoes_html})
    else:
        form = PersonaForm()
    return render(request, 'persona_form.html', {'form': form})