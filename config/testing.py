"""Apoio para os testes: hosts fixos, MEDIA_ROOT temporário e imagens geradas em memória."""

import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image

SITE = "localhost"
PAINEL = "painel.localhost"
SENHA_TESTE = "Teste-Painel-2026!"


def imagem_bytes(formato="JPEG", tamanho=(800, 600), cor=(120, 40, 200), modo="RGB", orientacao=None):
    imagem = Image.new(modo, tamanho, cor)
    buffer = BytesIO()
    opcoes = {}
    if orientacao:
        exif = Image.Exif()
        exif[0x0112] = orientacao
        opcoes["exif"] = exif
    imagem.save(buffer, format=formato, **opcoes)
    return buffer.getvalue()


def arquivo_imagem(nome="foto.jpg", formato="JPEG", content_type="image/jpeg", **kwargs):
    return SimpleUploadedFile(nome, imagem_bytes(formato=formato, **kwargs), content_type=content_type)


@override_settings(
    SITE_HOST=SITE,
    PAINEL_HOST=PAINEL,
    ALLOWED_HOSTS=[SITE, PAINEL, "testserver"],
)
class HostsTestCase(TestCase):
    """TestCase com os dois hosts e MEDIA_ROOT temporário (apagado no fim de cada teste)."""

    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp(prefix="creative-media-")
        media = override_settings(MEDIA_ROOT=self.media_root)
        media.enable()
        self.addCleanup(media.disable)
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)

    def site_get(self, url, **kwargs):
        return self.client.get(url, HTTP_HOST=SITE, **kwargs)

    def site_post(self, url, data=None, **kwargs):
        return self.client.post(url, data or {}, HTTP_HOST=SITE, **kwargs)

    def painel_get(self, url, **kwargs):
        return self.client.get(url, HTTP_HOST=PAINEL, **kwargs)

    def painel_post(self, url, data=None, **kwargs):
        return self.client.post(url, data or {}, HTTP_HOST=PAINEL, **kwargs)

    def criar_dono(self, **kwargs):
        dados = {"username": "dono", "password": SENHA_TESTE, "is_staff": True, **kwargs}
        return get_user_model().objects.create_user(**dados)

    def entrar_como_dono(self):
        self.dono = self.criar_dono()
        self.client.force_login(self.dono)
        return self.dono
