"""Gera a versão estática do site (index.html na raiz do repositório) para o GitHub Pages.

O GitHub Pages só serve arquivos; não roda Django. Este comando renderiza a home com os dados
atuais do banco (configurações, depoimentos ativos) e grava:

    index.html         a home, com caminhos relativos (funciona em usuario.github.io/repositorio/)
    .nojekyll          para o GitHub Pages servir os arquivos como estão

O portfólio NÃO vem do banco: é montado por scripts/montar_portfolio.py a partir da pasta fotos/
e do arquivo modo-fotos.txt (o GitHub Actions roda esse script a cada push).
A pasta static/ já está na raiz do repositório e é usada diretamente pelo index.html.
Sem servidor, o formulário de contato abre o WhatsApp (ou o e-mail) com a mensagem preenchida.
"""

import re
import shutil
import sys
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.test import RequestFactory

from apps.institucional.forms import ContatoForm
from apps.institucional.services import contexto_home
from apps.institucional.views import TEMPLATE_HOME

sys.path.insert(0, str(Path(settings.BASE_DIR) / "scripts"))
from montar_portfolio import montar  # noqa: E402

PASTA_FOTOS = "fotos"


class Command(BaseCommand):
    help = "Gera o index.html estático (portfólio vindo de fotos/) para o GitHub Pages."

    def add_arguments(self, parser):
        parser.add_argument(
            "--saida",
            default=str(settings.BASE_DIR),
            help="Pasta de saída (padrão: raiz do repositório).",
        )
        parser.add_argument(
            "--url-publica",
            default="",
            help="Endereço público do site (ex.: https://usuario.github.io/Site_Filipe/), usado nas tags og:.",
        )

    def handle(self, *args, **opcoes):
        saida = Path(opcoes["saida"]).resolve()
        saida.mkdir(parents=True, exist_ok=True)
        url_publica = opcoes["url_publica"].strip()
        if url_publica and not url_publica.endswith("/"):
            url_publica += "/"

        request = RequestFactory().get("/", HTTP_HOST=settings.SITE_HOST)
        contexto = contexto_home(ContatoForm())
        contexto["modo_estatico"] = True
        html = render_to_string(TEMPLATE_HOME, contexto, request=request)

        html = self._caminhos_relativos(html, request.build_absolute_uri("/"), url_publica)
        (saida / "index.html").write_text(html, encoding="utf-8")
        (saida / ".nojekyll").write_text("", encoding="utf-8")

        base = Path(settings.BASE_DIR).resolve()
        if saida != base:
            for pasta in ("static", PASTA_FOTOS):
                destino = saida / pasta
                shutil.rmtree(destino, ignore_errors=True)
                if (base / pasta).is_dir():
                    shutil.copytree(base / pasta, destino)
            arquivo_modo = base / "modo-fotos.txt"
            if arquivo_modo.exists():
                shutil.copy2(arquivo_modo, saida / arquivo_modo.name)

        montar(saida)
        self.stdout.write(self.style.SUCCESS(f"index.html gerado em {saida}."))

    @staticmethod
    def _caminhos_relativos(html, origem_render, url_publica):
        # Tags og: precisam de URL absoluta: usa a pública, ou remove a origem do render.
        html = html.replace(origem_render, url_publica)
        media = settings.MEDIA_URL
        html = re.sub(r'(href|src|content)="' + re.escape(settings.STATIC_URL), r'\1="static/', html)
        html = re.sub(r'(href|src|content)="' + re.escape(media), rf'\1="{PASTA_FOTOS}/', html)
        # Links internos "/#secao" viram "#secao" (o site pode estar em subpasta no Pages).
        html = html.replace('href="/#', 'href="#')
        return html
