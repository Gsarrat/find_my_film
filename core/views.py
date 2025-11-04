import json
import os

import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.db.models import Avg, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import PersonaForm
from .models import FilmeAssistido, Persona, Post, Recomendacao
from .recommender import gerar_recomendacoes
from .utils import buscar_filmes_imdb



TMDB_API_KEY = os.getenv("TMDB_API_KEY")

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
            login(request, user)  
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

            cache_key = f"recomendacoes_{user.id}_{dados['genero_favorito']}_{dados['humor']}"
            recomendacoes_html = cache.get(cache_key)
            if not recomendacoes_html:
                recomendacoes_html = gerar_recomendacoes(dados, user=request.user)
                cache.set(cache_key, recomendacoes_html, timeout=3600)  

            Recomendacao.objects.create(persona=persona, filmes_html=recomendacoes_html)

            filmes_enriquecidos = buscar_filmes_imdb(recomendacoes_html)
            

            return render(request, 'recomendacoes.html', {
                'recomendacoes': filmes_enriquecidos,
            })
    else:
        form = PersonaForm(instance=persona)

    return render(request, 'persona_form.html', {'form': form})

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from .models import FilmeAssistido

@csrf_exempt
def marcar_assistido(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            titulo = data.get("titulo")
            nota = int(data.get("nota"))

            if not titulo or not (1 <= nota <= 5):
                return JsonResponse({"success": False, "error": "Dados inválidos."})

            filme, created = FilmeAssistido.objects.get_or_create(
                usuario=request.user,
                titulo=titulo,
                defaults={"nota": nota}
            )
            if not created:
                filme.nota = nota
                filme.save()

            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Método inválido."})


@login_required
def dashboard_view(request):
    user = request.user

    persona = Persona.objects.filter(user=user).first()

    recomendacoes = Recomendacao.objects.filter(persona__user=user).order_by('-data_criacao')[:5]

    filmes = FilmeAssistido.objects.filter(user=user).order_by('-data_assistido')

    total_filmes = filmes.count()
    nota_media = filmes.aggregate(media=Avg('nota'))['media'] or 0

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

def buscar_filme(request):
    """Consulta TMDb e retorna resultados JSON incluindo user_rating (se logado)."""
    termo = request.GET.get("q", "")
    if not termo or len(termo) < 2:
        return JsonResponse({"results": []})

    try:
        r = requests.get(
            "https://api.themoviedb.org/3/search/movie",
            params={
                "api_key": TMDB_API_KEY,
                "query": termo,
                "language": "pt-BR",
                "include_adult": "false"
            },
            timeout=5
        )
        data = r.json()
        filmes = []

        for f in data.get("results", [])[:8]:
            poster = f"https://image.tmdb.org/t/p/w500{f.get('poster_path')}" if f.get("poster_path") else ""
            ano = f.get("release_date", "")[:4] if f.get("release_date") else "N/A"
            tmdb_id = f.get("id")
            detalhes = requests.get(
                f"https://api.themoviedb.org/3/movie/{tmdb_id}",
                params={"api_key": TMDB_API_KEY, "append_to_response": "external_ids"},
                timeout=5
            ).json()
            imdb_id = detalhes.get("external_ids", {}).get("imdb_id")

            
            user_rating = None
            if request.user.is_authenticated:
                fa = FilmeAssistido.objects.filter(user=request.user, imdb_id=imdb_id).first()
                if not fa:
                    fa = FilmeAssistido.objects.filter(user=request.user, titulo=f.get("title")).first()
                if fa:
                    user_rating = fa.nota  

            filmes.append({
                "titulo": f.get("title"),
                "ano": ano,
                "poster": poster,
                "tmdb_id": tmdb_id,
                "imdb_id": imdb_id,
                "link": f"https://www.imdb.com/title/{imdb_id}" if imdb_id else "#",
                "user_rating": user_rating 
            })

        return JsonResponse({"results": filmes})

    except Exception as e:
        return JsonResponse({"error": str(e), "results": []})
    
    
@login_required
@require_POST
def marcar_assistido_api(request):
    """
    Recebe JSON {titulo, nota, tmdb_id, imdb_id} e salva/atualiza FilmeAssistido.
    """
    try:
        data = json.loads(request.body or "{}")
        titulo = (data.get("titulo") or "").strip()
        nota = int(data.get("nota") or 0)
        tmdb_id = data.get("tmdb_id")
        imdb_id = data.get("imdb_id")

        if not titulo or not (1 <= nota <= 5):
            return JsonResponse({"success": False, "error": "Dados inválidos."}, status=400)

        obj, created = FilmeAssistido.objects.update_or_create(
            user=request.user,
            imdb_id=imdb_id if imdb_id else None,
            titulo=titulo,
            defaults={"nota": nota}
        )
        return JsonResponse({"success": True, "created": created})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
    

def movie_details(request):
    """
    Retorna JSON com detalhes do filme via TMDb (overview, cast, diretor, runtime, genres, imdb_id, trailer).
    Exige query param: tmdb_id
    """
    tmdb_id = request.GET.get("tmdb_id")
    if not tmdb_id:
        return JsonResponse({"error": "tmdb_id required"}, status=400)

    try:
        detalhes = requests.get(
            f"https://api.themoviedb.org/3/movie/{tmdb_id}",
            params={"api_key": TMDB_API_KEY, "append_to_response": "external_ids,credits,videos", "language": "pt-BR"},
            timeout=6
        ).json()

        cast = []
        director = None
        for member in detalhes.get("credits", {}).get("cast", [])[:6]:
            cast.append({"name": member.get("name"), "character": member.get("character")})

        for crew in detalhes.get("credits", {}).get("crew", []):
            if crew.get("job") == "Director":
                director = crew.get("name")
                break

        trailer_url = None
        for v in detalhes.get("videos", {}).get("results", []):
            if v.get("type") == "Trailer" and v.get("site") == "YouTube":
                trailer_url = f"https://www.youtube.com/watch?v={v.get('key')}"
                break

        response = {
            "titulo": detalhes.get("title"),
            "original_title": detalhes.get("original_title"),
            "ano": detalhes.get("release_date", "")[:4],
            "runtime": detalhes.get("runtime"), 
            "genres": [g.get("name") for g in detalhes.get("genres", [])],
            "sinopse": detalhes.get("overview"),
            "poster": f"https://image.tmdb.org/t/p/w500{detalhes.get('poster_path')}" if detalhes.get('poster_path') else "",
            "backdrop": f"https://image.tmdb.org/t/p/w780{detalhes.get('backdrop_path')}" if detalhes.get('backdrop_path') else "",
            "imdb_id": detalhes.get("external_ids", {}).get("imdb_id"),
            "vote_average": detalhes.get("vote_average"),
            "vote_count": detalhes.get("vote_count"),
            "cast": cast,
            "director": director,
            "tmdb_id": tmdb_id,
            "trailer": trailer_url, 
        }
        return JsonResponse(response)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)