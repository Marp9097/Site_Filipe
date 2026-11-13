import re
from urllib.parse import quote

from apps.portfolio.models import Categoria
from apps.portfolio.services import fotos_publicadas

from .models import ConfiguracaoSite, Depoimento, MensagemContato

TEXTO_WHATSAPP_ORCAMENTO = "Olá! Gostaria de solicitar um orçamento."
ASSUNTO_RESPOSTA_EMAIL = "Re: Seu contato pelo site da Creative Comunicação"

SERVICOS = [
    {
        "titulo": "Letreiros e Fachadas",
        "descricao": "Letreiros luminosos, fachadas em ACM, letras caixa, neon LED e muito mais para destacar seu negócio.",
        "icone": "fachadas",
    },
    {
        "titulo": "Adesivos e Envelopamento",
        "descricao": "Adesivos personalizados, envelopamento de veículos, vitrines e superfícies diversas com alta qualidade.",
        "icone": "adesivos",
    },
    {
        "titulo": "Personalização",
        "descricao": "Placas de sinalização, totens publicitários, painéis e estruturas para comunicação visual externa.",
        "icone": "personalizacao",
    },
    {
        "titulo": "Estruturas Metálicas",
        "descricao": "Estruturas metálicas sob medida para fachadas, totens e painéis, com fabricação e instalação.",
        "icone": "estruturas",
    },
    {
        "titulo": "Impressão Digital",
        "descricao": "Impressão em grande formato, banners, lonas, adesivos, papel de parede e materiais promocionais.",
        "icone": "impressao",
    },
]


def somente_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def whatsapp_url(numero, texto=TEXTO_WHATSAPP_ORCAMENTO):
    """Link wa.me com o texto codificado na URL. Retorna '' se não houver número."""
    digitos = somente_digitos(numero)
    if not digitos:
        return ""
    return f"https://wa.me/{digitos}?text={quote(texto, safe='')}"


def numero_whatsapp_brasil(telefone):
    """Converte um telefone digitado pelo visitante em número wa.me (DDI 55). Retorna '' se inválido."""
    digitos = somente_digitos(telefone)
    if len(digitos) in (10, 11):
        return f"55{digitos}"
    if digitos.startswith("55") and len(digitos) in (12, 13):
        return digitos
    return ""


def resposta_whatsapp_url(mensagem):
    numero = numero_whatsapp_brasil(mensagem.telefone)
    if not numero:
        return ""
    texto = f"Olá, {mensagem.nome}! Aqui é da Creative Comunicação. Recebemos sua mensagem pelo site."
    return whatsapp_url(numero, texto)


def mailto_url(mensagem):
    return f"mailto:{mensagem.email}?subject={quote(ASSUNTO_RESPOSTA_EMAIL, safe='')}"


def marcar_como_lida(mensagem):
    if not mensagem.lida:
        mensagem.lida = True
        mensagem.save(update_fields=["lida"])
    return mensagem


def contexto_home(form):
    config = ConfiguracaoSite.atual()
    return {
        "config": config,
        "servicos": SERVICOS,
        "categorias": Categoria.objects.filter(fotos__publicada=True).distinct().order_by("ordem", "nome"),
        "fotos": fotos_publicadas(),
        "depoimentos": Depoimento.objects.filter(ativo=True).order_by("ordem", "id"),
        "form": form,
        "whatsapp_url": whatsapp_url(config.whatsapp),
    }


def nao_lidas():
    return MensagemContato.objects.filter(lida=False).count()
