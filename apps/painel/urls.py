from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "painel"

urlpatterns = [
    path("entrar/", views.EntrarView.as_view(), name="entrar"),
    path("sair/", LogoutView.as_view(next_page="/entrar/"), name="sair"),
    path("", views.inicio, name="inicio"),
    path("fotos/", views.fotos, name="fotos"),
    path("fotos/<int:pk>/editar/", views.foto_editar, name="foto_editar"),
    path("fotos/<int:pk>/excluir/", views.foto_excluir, name="foto_excluir"),
    path("categorias/", views.categorias, name="categorias"),
    path("categorias/<int:pk>/excluir/", views.categoria_excluir, name="categoria_excluir"),
    path("configuracoes/", views.configuracoes, name="configuracoes"),
    path("depoimentos/", views.depoimentos, name="depoimentos"),
    path("depoimentos/<int:pk>/editar/", views.depoimento_editar, name="depoimento_editar"),
    path("depoimentos/<int:pk>/excluir/", views.depoimento_excluir, name="depoimento_excluir"),
    path("mensagens/", views.mensagens, name="mensagens"),
    path("mensagens/<int:pk>/", views.mensagem_detalhe, name="mensagem_detalhe"),
]
