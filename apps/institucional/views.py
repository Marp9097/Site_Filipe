from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import ContatoForm
from .services import contexto_home

TEMPLATE_HOME = "institucional/home.html"
MENSAGEM_ENVIADA = "Mensagem enviada! Em breve entramos em contato."


@require_GET
def home(request):
    return render(request, TEMPLATE_HOME, contexto_home(ContatoForm()))


@require_POST
def contato(request):
    form = ContatoForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, MENSAGEM_ENVIADA)
        return redirect("/#contato")
    return render(request, TEMPLATE_HOME, contexto_home(form))
