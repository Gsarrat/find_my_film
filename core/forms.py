from django import forms
from .models import Persona

class PersonaForm(forms.ModelForm):
    nome = forms.CharField(label='Seu nome', max_length=100)
    genero_favorito = forms.CharField(
        label='Gêneros de filmes preferidos (ex: ação, drama, comédia)', 
        max_length=200
    )
    humor = forms.ChoiceField(
        label='Como você está se sentindo hoje?', 
        choices=[
            ('feliz', 'Feliz'),
            ('triste', 'Triste'),
            ('reflexivo', 'Reflexivo'),
            ('animado', 'Animado'),
            ('entediado', 'Entediado'),
        ]
    )
    tempo_disponivel = forms.ChoiceField(
        label='Quanto tempo você quer gastar assistindo?', 
        choices=[
            ('curto', 'Menos de 1h30'),
            ('medio', 'Entre 1h30 e 2h'),
            ('longo', 'Mais de 2h'),
        ]
    )
    anos = forms.ChoiceField(
    label='Período dos filmes preferido:',
    choices=[
        ('todos', 'Qualquer ano'),
        ('antigos', 'Antes de 2000'),
        ('recentes', 'De 2000 a 2020'),
        ('atuais', 'De 2020 até hoje'),
    ]
    )
    
    class Meta:
        model = Persona
        fields = ['nome', 'genero_favorito', 'humor', 'tempo_disponivel']
