import os
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def gerar_recomendacoes(persona_dados):
    """
    Gera recomendações de filmes com base na persona do usuário
    usando o modelo via OpenRouter (compatível com OpenAI).
    """

    # 🔹 Configuração da API OpenRouter
    # Você deve definir no .env:
    #   OPENROUTER_API_KEY=...
    #   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
    api_key = getattr(settings, "OPENROUTER_API_KEY", None)
    base_url = getattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    if not api_key:
        raise ValueError("A chave OPENROUTER_API_KEY não está configurada no .env ou settings.py")

    # 🔹 Criação do LLM com LangChain + OpenRouter
    llm = ChatOpenAI(
        model="gpt-4o-mini",          # ou outro modelo disponível no OpenRouter
        api_key=api_key,
        base_url=base_url,            # importante para redirecionar para o OpenRouter
        temperature=0.7,
        max_tokens=700,
    )

    # 🔹 Prompt com template dinâmico
    prompt = ChatPromptTemplate.from_template("""
    Você é um assistente especialista em cinema.
    Um usuário com as seguintes características pediu recomendações de filmes:

    - Nome: {nome}
    - Gêneros preferidos: {genero_favorito}
    - Humor atual: {humor}
    - Tempo disponível: {tempo_disponivel}

    Gere uma lista com 5 filmes recomendados, cada um com:
    - 🎬 Título
    - 🎭 Gênero principal
    - 🕒 Duração aproximada
    - 📝 Breve descrição (2 linhas)
    - 💡 Por que é uma boa escolha para essa persona

    Responda em formato HTML limpo (sem Markdown).
    """)

    # 🔹 Encadeia o prompt com o modelo
    chain = prompt | llm

    # 🔹 Executa a geração
    resposta = chain.invoke(persona_dados)

    return resposta.content
