import os
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from .models import FilmeAssistido, Persona
from datetime import datetime


def gerar_recomendacoes(persona_dados, user=None):
    """
    Gera recomendações de filmes personalizadas com base:
    - Na persona atual
    - Nos filmes assistidos e notas anteriores
    - Nos anos desejados
    - E na IA (via OpenRouter)
    """

    api_key = getattr(settings, "OPENROUTER_API_KEY", None)
    base_url = getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    if not api_key:
        raise ValueError("A chave OPENROUTER_API_KEY não está configurada no .env ou settings.py")

    # Extrai dados da persona
    genero = persona_dados.get("genero_favorito", "qualquer gênero")
    humor = persona_dados.get("humor", "neutro")
    tempo = persona_dados.get("tempo_disponivel", "qualquer duração")
    anos = persona_dados.get("anos", "todos os períodos")

    # Coleta filmes já assistidos
    filmes_assistidos = []
    if user:
        filmes_assistidos = list(
            FilmeAssistido.objects.filter(user=user).values_list("titulo", "nota")
        )

    # Divide entre bons e ruins
    filmes_bons = [f for f, nota in filmes_assistidos if nota >= 3]
    filmes_ruins = [f for f, nota in filmes_assistidos if nota < 3]

    # Monta resumo do histórico
    historico_texto = ""
    if filmes_assistidos:
        historico_texto = f"""
        O usuário já assistiu {len(filmes_assistidos)} filmes.
        Alguns que ele gostou muito: {', '.join(filmes_bons[:5]) or 'nenhum ainda'}.
        Alguns que ele não gostou: {', '.join(filmes_ruins[:5]) or 'nenhum'}.
        Não recomende filmes já assistidos.
        """
    else:
        historico_texto = "O usuário ainda não assistiu filmes registrados."

    # Configura modelo OpenRouter
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        max_tokens=800,
    )

    # Prompt contextualizado
    prompt = ChatPromptTemplate.from_template("""
    Você é um curador de cinema que recomenda filmes personalizados.

    Dados do usuário:
    - Gêneros preferidos: {genero}
    - Humor atual: {humor}
    - Tempo disponível: {tempo}
    - Período desejado: {anos}
    - Histórico de visualização: 
    {historico}

    Tarefa:
    Recomende **5 filmes** que combinem com o perfil e preferências do usuário,
    evitando qualquer título já assistido. Dê prioridade a filmes parecidos com
    os que ele deu nota alta e evite filmes semelhantes aos que ele não gostou.

    Para cada filme, inclua:
    - Título
    - Gênero principal
    - Duração aproximada
    - Ano de lançamento
    - Motivo da recomendação (1 frase curta)

    Retorne o resultado **em HTML limpo**, sem Markdown.
    """)
    print(prompt)

    chain = prompt | llm

    resposta = chain.invoke({
        "genero": genero,
        "humor": humor,
        "tempo": tempo,
        "anos": anos,
        "historico": historico_texto
    })
    print(resposta)
    return resposta.content
