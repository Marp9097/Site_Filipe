import os

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.portfolio.models import Categoria, Foto
from config.testing import HostsTestCase, arquivo_imagem, imagem_bytes


def _criar_foto(publicada=True, categoria=None, nome="trabalho.jpg"):
    foto = Foto(publicada=publicada, categoria=categoria)
    foto.imagem.save(nome, ContentFile(imagem_bytes()), save=True)
    return foto


class UploadDeFotosTests(HostsTestCase):
    def setUp(self):
        super().setUp()
        self.entrar_como_dono()
        self.fachadas = Categoria.objects.get(slug="letreiros-e-fachadas")

    def test_ca11_envia_3_imagens_jpg_png_webp(self):
        arquivos = [
            arquivo_imagem("grande.jpg", tamanho=(3000, 2000)),
            arquivo_imagem("logo.png", formato="PNG", content_type="image/png", tamanho=(1200, 2400)),
            arquivo_imagem("obra.webp", formato="WEBP", content_type="image/webp", tamanho=(640, 480)),
        ]
        resposta = self.painel_post(
            "/fotos/", {"imagens": arquivos, "categoria": self.fachadas.pk}, follow=True
        )
        self.assertEqual(resposta.redirect_chain[-1], ("/fotos/", 302))
        self.assertContains(resposta, "3 fotos enviadas.")
        fotos = Foto.objects.all()
        self.assertEqual(fotos.count(), 3)
        for foto in fotos:
            with self.subTest(foto=foto.imagem.name):
                self.assertTrue(foto.publicada)
                self.assertEqual(foto.categoria, self.fachadas)
                self.assertTrue(foto.imagem.name.startswith("portfolio/"))
                with Image.open(foto.imagem.path) as imagem:
                    self.assertLessEqual(max(imagem.size), 1920)

    def test_ca11_uma_foto_mensagem_no_singular(self):
        resposta = self.painel_post("/fotos/", {"imagens": [arquivo_imagem()]}, follow=True)
        self.assertContains(resposta, "1 foto enviada.")
        self.assertIsNone(Foto.objects.get().categoria)

    def test_ca12_pdf_e_rejeitado_e_nada_e_salvo(self):
        pdf = SimpleUploadedFile("orcamento.pdf", b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n", content_type="application/pdf")
        resposta = self.painel_post("/fotos/", {"imagens": [arquivo_imagem(), pdf]})
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Foto.objects.exists())
        erros = resposta.context["form"].errors["imagens"]
        self.assertTrue(any("orcamento.pdf" in erro and "não é uma imagem válida" in erro for erro in erros))
        self.assertContains(resposta, "não é uma imagem válida")

    def test_ca12_e_cap3_txt_renomeado_para_jpg_e_rejeitado(self):
        falso = SimpleUploadedFile("foto.jpg", b"isto nao e uma imagem", content_type="image/jpeg")
        resposta = self.painel_post("/fotos/", {"imagens": [falso]})
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Foto.objects.exists())
        self.assertIn("“foto.jpg” não é uma imagem válida", resposta.context["form"].errors["imagens"][0])

    def test_ca12_arquivo_maior_que_10mb_e_rejeitado(self):
        grande = SimpleUploadedFile(
            "enorme.jpg", imagem_bytes() + b"\0" * (10 * 1024 * 1024), content_type="image/jpeg"
        )
        resposta = self.painel_post("/fotos/", {"imagens": [grande]})
        self.assertFalse(Foto.objects.exists())
        erro = resposta.context["form"].errors["imagens"][0]
        self.assertIn("enorme.jpg", erro)
        self.assertIn("O limite é 10 MB", erro)

    def test_ca12_mais_de_20_arquivos_e_rejeitado(self):
        arquivos = [arquivo_imagem(f"f{i}.jpg", tamanho=(20, 20)) for i in range(21)]
        resposta = self.painel_post("/fotos/", {"imagens": arquivos})
        self.assertFalse(Foto.objects.exists())
        self.assertIn("no máximo 20 fotos", resposta.context["form"].errors["imagens"][0])

    def test_ca12_envio_sem_arquivo_mostra_erro(self):
        resposta = self.painel_post("/fotos/", {})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Selecione ao menos uma foto.", resposta.context["form"].errors["imagens"])

    def test_contexto_da_tela_de_fotos(self):
        _criar_foto(categoria=self.fachadas)
        _criar_foto()
        resposta = self.painel_get("/fotos/")
        self.assertTemplateUsed(resposta, "painel/fotos.html")
        self.assertEqual(len(resposta.context["fotos"]), 2)
        self.assertEqual(resposta.context["categorias"].count(), 5)
        self.assertIsNone(resposta.context["filtro_categoria"])
        self.assertIn("imagens", resposta.context["form"].fields)
        self.assertContains(resposta, 'enctype="multipart/form-data"')
        self.assertContains(resposta, "multiple")

    def test_filtro_por_categoria(self):
        _criar_foto(categoria=self.fachadas)
        _criar_foto()
        resposta = self.painel_get(f"/fotos/?categoria={self.fachadas.pk}")
        self.assertEqual(resposta.context["filtro_categoria"], self.fachadas)
        self.assertEqual([f.categoria for f in resposta.context["fotos"]], [self.fachadas])

    def test_lista_de_fotos_sem_n_mais_1(self):
        for _ in range(3):
            _criar_foto(categoria=self.fachadas)
        resposta = self.painel_get("/fotos/")
        with self.assertNumQueries(0):
            [foto.categoria.nome for foto in resposta.context["fotos"]]


class PublicarEExcluirFotoTests(HostsTestCase):
    def setUp(self):
        super().setUp()
        self.entrar_como_dono()

    def test_ca13_publicar_no_painel_faz_a_foto_aparecer_no_site(self):
        foto = _criar_foto(publicada=False)
        self.assertNotIn(foto, self.site_get("/").context["fotos"])
        resposta = self.painel_get(f"/fotos/{foto.pk}/editar/")
        self.assertTemplateUsed(resposta, "painel/foto_form.html")
        self.assertEqual(resposta.context["foto"], foto)
        self.painel_post(f"/fotos/{foto.pk}/editar/", {"titulo": "Fachada ACM", "categoria": "", "publicada": "on", "ordem": 0})
        foto.refresh_from_db()
        self.assertTrue(foto.publicada)
        self.assertEqual(foto.titulo, "Fachada ACM")
        site = self.site_get("/")
        self.assertIn(foto, site.context["fotos"])
        self.assertContains(site, foto.imagem.url)

    def test_ca13_despublicar_tira_a_foto_do_site(self):
        foto = _criar_foto(publicada=True)
        self.painel_post(f"/fotos/{foto.pk}/editar/", {"titulo": "", "categoria": "", "ordem": 0})
        foto.refresh_from_db()
        self.assertFalse(foto.publicada)
        self.assertNotContains(self.site_get("/"), foto.imagem.url)

    def test_ca14_excluir_remove_do_banco_e_do_disco(self):
        foto = _criar_foto()
        caminho = foto.imagem.path
        self.assertTrue(os.path.exists(caminho))
        resposta = self.painel_post(f"/fotos/{foto.pk}/excluir/", follow=True)
        self.assertEqual(resposta.redirect_chain[-1], ("/fotos/", 302))
        self.assertContains(resposta, "Foto excluída.")
        self.assertFalse(Foto.objects.filter(pk=foto.pk).exists())
        self.assertFalse(os.path.exists(caminho))

    def test_ca14_excluir_exige_post(self):
        foto = _criar_foto()
        self.assertEqual(self.painel_get(f"/fotos/{foto.pk}/excluir/").status_code, 405)
        self.assertTrue(Foto.objects.filter(pk=foto.pk).exists())

    def test_foto_inexistente_da_404(self):
        self.assertEqual(self.painel_get("/fotos/999/editar/").status_code, 404)
        self.assertEqual(self.painel_post("/fotos/999/excluir/").status_code, 404)


class CategoriasTests(HostsTestCase):
    def setUp(self):
        super().setUp()
        self.entrar_como_dono()

    def test_lista_com_total_de_fotos(self):
        fachadas = Categoria.objects.get(slug="letreiros-e-fachadas")
        _criar_foto(categoria=fachadas)
        _criar_foto(categoria=fachadas)
        resposta = self.painel_get("/categorias/")
        self.assertTemplateUsed(resposta, "painel/categorias.html")
        totais = {c.slug: c.total_fotos for c in resposta.context["categorias"]}
        self.assertEqual(totais["letreiros-e-fachadas"], 2)
        self.assertEqual(totais["impressao-digital"], 0)

    def test_cria_categoria_com_slug(self):
        resposta = self.painel_post("/categorias/", {"nome": "Placas e Totens", "ordem": 6}, follow=True)
        self.assertContains(resposta, "Categoria “Placas e Totens” criada.")
        self.assertTrue(Categoria.objects.filter(slug="placas-e-totens").exists())

    def test_nome_repetido_mostra_erro(self):
        resposta = self.painel_post("/categorias/", {"nome": "impressão digital", "ordem": 0})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Já existe uma categoria com esse nome.", resposta.context["form"].errors["nome"])

    def test_excluir_categoria_deixa_fotos_sem_categoria(self):
        fachadas = Categoria.objects.get(slug="letreiros-e-fachadas")
        foto = _criar_foto(categoria=fachadas)
        resposta = self.painel_post(f"/categorias/{fachadas.pk}/excluir/")
        self.assertRedirects(resposta, "/categorias/", fetch_redirect_response=False)
        foto.refresh_from_db()
        self.assertIsNone(foto.categoria)
        self.assertFalse(Categoria.objects.filter(pk=fachadas.pk).exists())
