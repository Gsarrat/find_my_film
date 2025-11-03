import os
import re
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def traduzir_titulo(titulo):
    """Traduz o título para inglês antes da busca no TMDb."""
    try:
        traducao = GoogleTranslator(source="auto", target="en").translate(titulo)
        print(f"🌐 '{titulo}' → '{traducao}'")
        return traducao
    except Exception as e:
        print(f"⚠️ Erro ao traduzir '{titulo}': {e}")
        return titulo


def buscar_filmes_imdb(html_text):
    """
    Extrai títulos do HTML da IA, traduz e busca dados reais no TMDb.
    Retorna lista de filmes com título, ano, poster, sinopse e link IMDb.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    filmes = []

    texto = soup.get_text(separator="\n").strip()
    padroes = [
        r"🎬\s*([^:\n]+)",
        r"Título[:\-]\s*([^\n]+)",
        r"^([A-Z][A-Za-z0-9 ,'\-]+)$"
    ]

    encontrados = set()
    for padrao in padroes:
        for match in re.findall(padrao, texto, flags=re.MULTILINE):
            titulo = match.strip()
            if len(titulo) < 3 or len(titulo.split()) > 8:
                continue
            encontrados.add(titulo)

    print(f"🎯 Títulos extraídos da IA: {list(encontrados)}")

    if not encontrados:
        print("⚠️ Nenhum título reconhecido no texto da IA.")
        return []

    for titulo in encontrados:
        try:
            titulo_en = traduzir_titulo(titulo)
            print(f"🔍 Buscando no TMDb: {titulo_en}")

            r = requests.get(
                "https://api.themoviedb.org/3/search/movie",
                params={"api_key": TMDB_API_KEY, "query": titulo_en, "language": "pt-BR"}
            )
            data = r.json()

            if data.get("results"):
                filme = data["results"][0]
                imdb_id = None

                # tenta buscar o IMDb ID via movie details
                detalhes = requests.get(
                    f"https://api.themoviedb.org/3/movie/{filme['id']}",
                    params={"api_key": TMDB_API_KEY, "append_to_response": "external_ids", "language": "pt-BR"}
                ).json()

                imdb_id = detalhes.get("external_ids", {}).get("imdb_id")
                link_imdb = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else "#"

                filmes.append({
                    "titulo": filme["title"],
                    "ano": filme.get("release_date", "")[:4],
                    "poster": f"https://image.tmdb.org/t/p/w500{filme.get('poster_path', '')}",
                    "link": link_imdb,
                    "sinopse": filme.get("overview", ""),
                })
                print(f"✅ Encontrado: {filme['title']}")
            else:
                print(f"❌ Não encontrado: {titulo_en}")

        except Exception as e:
            print(f"⚠️ Erro ao buscar {titulo}: {e}")

    print(f"🎬 Total de filmes encontrados: {len(filmes)}")
    return filmes
