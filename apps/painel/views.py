from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.institucional import services as institucional
from apps.institucional.models import ConfiguracaoSite, Depoimento, MensagemContato
from apps.portfolio.models import Categoria, Foto
from apps.portfolio.services import processar_upload

from .decorators import staff_required
from .forms import (
    CategoriaForm,
    ConfiguracaoForm,
    DepoimentoForm,
    EntrarForm,
    FotoForm,
    FotoUploadForm,
)

MENSAGENS_POR_PAGINA = 20


class EntrarView(LoginView):
    template_name = "painel/entrar.html"
    authentication_form = EntrarForm
    redirect_authenticated_user = True


@staff_required
@require_GET
def inicio(request):
    contexto = {
        "total_fotos": Foto.objects.count(),
        "total_publicadas": Foto.objects.filter(publicada=True).count(),
        "nao_lidas": institucional.nao_lidas(),
        "ultimas_mensagens": MensagemContato.objects.order_by("-criada_em", "-id")[:5],
        "config": ConfiguracaoSite.atual(),
    }
    return render(request, "painel/inicio.html", contexto)


def _texto_fotos_enviadas(quantidade):
    return "1 foto enviada." if quantidade == 1 else f"{quantidade} fotos enviadas."


@staff_required
def fotos(request):
    if request.method == "POST":
        form = FotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                novas = processar_upload(form.cleaned_data["imagens"], form.cleaned_data["categoria"])
            except ValidationError as erro:
                form.add_error("imagens", erro)
            else:
                messages.success(request, _texto_fotos_enviadas(len(novas)))
                return redirect("painel:fotos")
    else:
        form = FotoUploadForm()

    lista = Foto.objects.select_related("categoria").order_by("ordem", "-criada_em")
    filtro_categoria = None
    categoria_id = request.GET.get("categoria", "")
    if categoria_id.isdigit():
        filtro_categoria = Categoria.objects.filter(pk=categoria_id).first()
        if filtro_categoria:
            lista = lista.filter(categoria=filtro_categoria)

    contexto = {
        "fotos": lista,
        "categorias": Categoria.objects.all(),
        "form": form,
        "filtro_categoria": filtro_categoria,
    }
    return render(request, "painel/fotos.html", contexto)


@staff_required
def foto_editar(request, pk):
    foto = get_object_or_404(Foto.objects.select_related("categoria"), pk=pk)
    form = FotoForm(request.POST or None, instance=foto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Foto atualizada.")
        return redirect("painel:fotos")
    return render(request, "painel/foto_form.html", {"foto": foto, "form": form})


@staff_required
@require_POST
def foto_excluir(request, pk):
    foto = get_object_or_404(Foto, pk=pk)
    foto.delete()
    messages.success(request, "Foto excluída.")
    return redirect("painel:fotos")


@staff_required
def categorias(request):
    form = CategoriaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        categoria = form.save()
        messages.success(request, f"Categoria “{categoria.nome}” criada.")
        return redirect("painel:categorias")
    contexto = {
        "categorias": Categoria.objects.annotate(total_fotos=Count("fotos")).order_by("ordem", "nome"),
        "form": form,
    }
    return render(request, "painel/categorias.html", contexto)


@staff_required
@require_POST
def categoria_excluir(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    nome = categoria.nome
    categoria.delete()
    messages.success(request, f"Categoria “{nome}” excluída. As fotos dela ficaram sem categoria.")
    return redirect("painel:categorias")


@staff_required
def configuracoes(request):
    config = ConfiguracaoSite.atual()
    form = ConfiguracaoForm(request.POST or None, instance=config)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Configurações salvas.")
        return redirect("painel:configuracoes")
    contexto = {
        "form": form,
        "opcoes_fundo": [
            {"valor": valor, "rotulo": rotulo, "classe": f"fundo--{valor}"}
            for valor, rotulo in ConfiguracaoSite.Fundo.choices
        ],
        "opcoes_modo": [
            {"valor": valor, "rotulo": rotulo} for valor, rotulo in ConfiguracaoSite.ModoFotos.choices
        ],
    }
    return render(request, "painel/configuracoes.html", contexto)


@staff_required
def depoimentos(request):
    form = DepoimentoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Depoimento criado.")
        return redirect("painel:depoimentos")
    contexto = {"depoimentos": Depoimento.objects.order_by("ordem", "id"), "form": form}
    return render(request, "painel/depoimentos.html", contexto)


@staff_required
def depoimento_editar(request, pk):
    depoimento = get_object_or_404(Depoimento, pk=pk)
    form = DepoimentoForm(request.POST or None, instance=depoimento)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Depoimento atualizado.")
        return redirect("painel:depoimentos")
    return render(request, "painel/depoimento_form.html", {"depoimento": depoimento, "form": form})


@staff_required
@require_POST
def depoimento_excluir(request, pk):
    depoimento = get_object_or_404(Depoimento, pk=pk)
    depoimento.delete()
    messages.success(request, "Depoimento excluído.")
    return redirect("painel:depoimentos")


@staff_required
@require_GET
def mensagens(request):
    paginator = Paginator(MensagemContato.objects.order_by("-criada_em", "-id"), MENSAGENS_POR_PAGINA)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "painel/mensagens.html", {"mensagens": page_obj.object_list, "page_obj": page_obj})


@staff_required
@require_GET
def mensagem_detalhe(request, pk):
    mensagem = institucional.marcar_como_lida(get_object_or_404(MensagemContato, pk=pk))
    contexto = {
        "mensagem": mensagem,
        "whatsapp_resposta_url": institucional.resposta_whatsapp_url(mensagem),
        "mailto_url": institucional.mailto_url(mensagem),
    }
    return render(request, "painel/mensagem.html", contexto)
