import os
import re
import requests
from bs4 import BeautifulSoup

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def buscar_filmes_imdb(html_text):
    """
    Extrai títulos do HTML da IA (seja em <h2> ou dentro de <li>) 
    e busca dados reais no TMDb.
    Retorna lista de filmes com título, ano, poster, sinopse e link IMDb.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    filmes = []

    #1️ Tenta pegar <h2> (formato anterior)
    titulos = [t.get_text(strip=True) for t in soup.find_all("h2")]

    #2️ Se não houver, procura "Título:" em <li> ou texto
    if not titulos:
        for li in soup.find_all("li"):
            texto = li.get_text(separator=" ").strip()
            match = re.search(r"Título[:\-]\s*([^\n<]+)", texto)
            if match:
                titulo = match.group(1).strip()
                if len(titulo) >= 2:
                    titulos.append(titulo)

    #3️ Remove duplicatas
    titulos = list(dict.fromkeys(titulos))

    if not titulos:
        print("⚠️ Nenhum título encontrado no HTML da IA.")
        print(html_text[:500]) 

    print(f"Títulos extraídos da IA: {titulos}")

    for titulo in titulos:
        try:
            print(f"Buscando no TMDb: {titulo}")
            r = requests.get(
                "https://api.themoviedb.org/3/search/movie",
                params={"api_key": TMDB_API_KEY, "query": titulo, "language": "pt-BR"}
            )
            data = r.json()

            if not data.get("results"):
                print(f"❌ Não encontrado: {titulo}")
                continue

            filme = data["results"][0]

            detalhes = requests.get(
                f"https://api.themoviedb.org/3/movie/{filme['id']}",
                params={"api_key": TMDB_API_KEY, "append_to_response": "external_ids", "language": "pt-BR"}
            ).json()

            imdb_id = detalhes.get("external_ids", {}).get("imdb_id")
            link_imdb = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else "#"

            filmes.append({
                "titulo": filme["title"],
                "ano": filme.get("release_date", "")[:4],
                "poster": f"https://image.tmdb.org/t/p/w500{filme.get('poster_path', '')}" if filme.get("poster_path") else "",
                "link": link_imdb,
                "sinopse": filme.get("overview", "Sem sinopse disponível."),
                "json": filme,
            })

            print(f"✅ Encontrado: {filme['title']}")

        except Exception as e:
            print(f"⚠️ Erro ao buscar {titulo}: {e}")

    print(f"Total de filmes encontrados: {len(filmes)}")
    return filmes
