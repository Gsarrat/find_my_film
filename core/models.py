from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    titulo = models.CharField(max_length=100)
    conteudo = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Persona(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    genero_favorito = models.CharField(max_length=200)
    humor = models.CharField(max_length=50)
    tempo_disponivel = models.CharField(max_length=20)
    ultima_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.genero_favorito}"


class Recomendacao(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    data_criacao = models.DateTimeField(auto_now_add=True)
    filmes_html = models.TextField()  

    def __str__(self):
        return f"Recomendações de {self.persona.user.username} em {self.data_criacao:%d/%m/%Y}"


class FilmeAssistido(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    imdb_id = models.CharField(max_length=20, blank=True, null=True)
    nota = models.PositiveIntegerField(default=0)
    data_assistido = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'titulo')

    def __str__(self):
        return f"{self.titulo} ({self.nota}/10)"