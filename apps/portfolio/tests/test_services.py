import os
from unittest import mock

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.portfolio import services
from apps.portfolio.models import Categoria, Foto
from config.testing import HostsTestCase, arquivo_imagem, imagem_bytes


class ValidarArquivosTests(HostsTestCase):
    def test_cap3_extensao_jpg_com_conteudo_texto_e_rejeitada(self):
        falso = SimpleUploadedFile("foto.jpg", b"texto qualquer", content_type="image/jpeg")
        with self.assertRaises(ValidationError) as erro:
            services.validar_arquivos([falso])
        self.assertIn("não é uma imagem válida", erro.exception.messages[0])

    def test_cap3_imagem_valida_com_extensao_errada_e_aceita_pelo_conteudo(self):
        png_com_nome_txt = arquivo_imagem("foto.txt", formato="PNG", content_type="text/plain")
        services.validar_arquivos([png_com_nome_txt])

    def test_formato_de_imagem_nao_aceito_e_rejeitado(self):
        gif = arquivo_imagem("anima.gif", formato="GIF", content_type="image/gif", modo="P", cor=1)
        with self.assertRaises(ValidationError) as erro:
            services.validar_arquivos([gif])
        self.assertIn("formato GIF", erro.exception.messages[0])

    def test_ca12_limite_de_tamanho(self):
        grande = SimpleUploadedFile("g.jpg", imagem_bytes() + b"\0" * (10 * 1024 * 1024), content_type="image/jpeg")
        with self.assertRaises(ValidationError) as erro:
            services.validar_arquivos([grande])
        self.assertIn("O limite é 10 MB", erro.exception.messages[0])

    def test_ca12_limite_de_quantidade(self):
        with self.assertRaises(ValidationError):
            services.validar_arquivos([arquivo_imagem(f"{i}.jpg", tamanho=(10, 10)) for i in range(21)])

    def test_reune_todos_os_erros(self):
        arquivos = [
            SimpleUploadedFile("a.jpg", b"x", content_type="image/jpeg"),
            SimpleUploadedFile("b.jpg", b"y", content_type="image/jpeg"),
        ]
        with self.assertRaises(ValidationError) as erro:
            services.validar_arquivos(arquivos)
        self.assertEqual(len(erro.exception.messages), 2)


class ProcessarUploadTests(HostsTestCase):
    def test_ca11_redimensiona_para_no_maximo_1920(self):
        categoria = Categoria.objects.get(slug="impressao-digital")
        fotos = services.processar_upload([arquivo_imagem("enorme.jpg", tamanho=(4000, 1000))], categoria)
        self.assertEqual(len(fotos), 1)
        with Image.open(fotos[0].imagem.path) as imagem:
            self.assertEqual(imagem.size, (1920, 480))
            self.assertEqual(imagem.format, "JPEG")
        self.assertEqual(fotos[0].categoria, categoria)
        self.assertTrue(fotos[0].publicada)

    def test_imagem_pequena_nao_e_ampliada(self):
        fotos = services.processar_upload([arquivo_imagem(tamanho=(300, 200))])
        with Image.open(fotos[0].imagem.path) as imagem:
            self.assertEqual(imagem.size, (300, 200))

    def test_corrige_rotacao_exif(self):
        foto_celular = arquivo_imagem("celular.jpg", tamanho=(400, 200), orientacao=6)
        fotos = services.processar_upload([foto_celular])
        with Image.open(fotos[0].imagem.path) as imagem:
            self.assertEqual(imagem.size, (200, 400))
            self.assertNotEqual(imagem.getexif().get(0x0112), 6)

    def test_png_com_transparencia_vira_webp(self):
        png = arquivo_imagem("logo.png", formato="PNG", content_type="image/png", modo="RGBA", cor=(0, 0, 0, 0))
        fotos = services.processar_upload([png])
        self.assertTrue(fotos[0].imagem.name.endswith(".webp"))

    def test_tudo_ou_nada_quando_um_arquivo_falha_no_processamento(self):
        arquivos = [arquivo_imagem("ok.jpg"), arquivo_imagem("ruim.jpg")]
        original = services.otimizar_imagem

        def falha_no_segundo(arquivo):
            if arquivo.name == "ruim.jpg":
                raise OSError("imagem truncada")
            return original(arquivo)

        with mock.patch.object(services, "otimizar_imagem", side_effect=falha_no_segundo):
            with self.assertRaises(ValidationError):
                services.processar_upload(arquivos)
        self.assertFalse(Foto.objects.exists())
        self.assertEqual(self._arquivos_em_media(), [])

    def _arquivos_em_media(self):
        return [nome for _raiz, _dirs, nomes in os.walk(self.media_root) for nome in nomes]


class ApagarArquivoTests(HostsTestCase):
    def test_ca14_excluir_foto_apaga_arquivo(self):
        foto = services.processar_upload([arquivo_imagem()])[0]
        caminho = foto.imagem.path
        self.assertTrue(os.path.exists(caminho))
        foto.delete()
        self.assertFalse(os.path.exists(caminho))

    def test_ca14_excluir_em_lote_apaga_arquivos(self):
        fotos = services.processar_upload([arquivo_imagem("a.jpg"), arquivo_imagem("b.jpg")])
        caminhos = [foto.imagem.path for foto in fotos]
        Foto.objects.all().delete()
        for caminho in caminhos:
            self.assertFalse(os.path.exists(caminho))


class TextoAlternativoTests(HostsTestCase):
    def test_usa_titulo_depois_categoria_depois_padrao(self):
        categoria = Categoria.objects.get(slug="impressao-digital")
        self.assertEqual(Foto(titulo="Banner da loja", categoria=categoria).texto_alternativo, "Banner da loja")
        self.assertEqual(
            Foto(categoria=categoria).texto_alternativo, "Impressão Digital: trabalho da Creative Comunicação"
        )
        self.assertEqual(Foto().texto_alternativo, "Trabalho da Creative Comunicação")


class CategoriasIniciaisTests(HostsTestCase):
    def test_data_migration_cria_as_5_categorias(self):
        self.assertEqual(
            list(Categoria.objects.values_list("nome", flat=True)),
            [
                "Letreiros e Fachadas",
                "Adesivos e Envelopamento",
                "Personalização",
                "Estruturas Metálicas",
                "Impressão Digital",
            ],
        )
