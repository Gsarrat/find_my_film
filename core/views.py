from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView

from django.contrib.auth.decorators import login_required
from django.core.cache import cache

from .models import Persona, Recomendacao


from .utils import buscar_filmes_imdb
from .models import FilmeAssistido
from .models import Post
from .forms import PersonaForm
from .recommender import gerar_recomendacoes
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import render
from .models import Persona, Recomendacao, FilmeAssistido


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

@login_required
def persona_view(request):
    user = request.user
    persona, _ = Persona.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = PersonaForm(request.POST, instance=persona)
        if form.is_valid():
            form.save()
            dados = form.cleaned_data

            # 🔹 Cache: verifica se já temos recomendação recente
            cache_key = f"recomendacoes_{user.id}_{dados['genero_favorito']}_{dados['humor']}"
            recomendacoes_html = cache.get(cache_key)
            if not recomendacoes_html:
                recomendacoes_html = gerar_recomendacoes(dados)
                cache.set(cache_key, recomendacoes_html, timeout=3600)  # 1h

            # 🔹 Salva recomendação no banco
            Recomendacao.objects.create(persona=persona, filmes_html=recomendacoes_html)

            # 🔹 Busca dados reais de filmes (IMDb / OMDb)
            filmes_enriquecidos = buscar_filmes_imdb(recomendacoes_html)
            print("Filmes enriquecidos:", filmes_enriquecidos)

            return render(request, 'recomendacoes.html', {
                'recomendacoes': filmes_enriquecidos,
            })
    else:
        form = PersonaForm(instance=persona)

    return render(request, 'persona_form.html', {'form': form})

@login_required
def marcar_assistido(request, titulo):
    if request.method == "POST":
        nota = int(request.POST.get("nota", 0))
        FilmeAssistido.objects.update_or_create(
            user=request.user,
            titulo=titulo,
            defaults={"nota": nota}
        )
        messages.success(request, f"Filme '{titulo}' marcado como assistido com nota {nota}/10!")
        return redirect('persona')
    return render(request, 'marcar_assistido.html', {'titulo': titulo})

@login_required
def dashboard_view(request):
    user = request.user

    # 🔹 Persona atual
    persona = Persona.objects.filter(user=user).first()

    # 🔹 Últimas recomendações
    recomendacoes = Recomendacao.objects.filter(persona__user=user).order_by('-data_criacao')[:5]

    # 🔹 Filmes assistidos
    filmes = FilmeAssistido.objects.filter(user=user).order_by('-data_assistido')

    # 🔹 Estatísticas
    total_filmes = filmes.count()
    nota_media = filmes.aggregate(media=Avg('nota'))['media'] or 0

    # Montar dados para o gráfico (exemplo: notas por filme)
    grafico_labels = [f.titulo for f in filmes]
    grafico_dados = [f.nota for f in filmes]

    context = {
        'persona': persona,
        'recomendacoes': recomendacoes,
        'filmes': filmes,
        'total_filmes': total_filmes,
        'nota_media': round(nota_media, 1),
        'grafico_labels': grafico_labels,
        'grafico_dados': grafico_dados,
    }

    return render(request, 'dashboard.html', context)