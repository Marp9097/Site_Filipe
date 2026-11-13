import re
from urllib.parse import quote

from django.core.files.base import ContentFile

from apps.institucional.models import ConfiguracaoSite, Depoimento
from apps.portfolio.models import Categoria, Foto
from config.testing import HostsTestCase, imagem_bytes


def _criar_foto(publicada=True, categoria=None):
    foto = Foto(publicada=publicada, categoria=categoria)
    foto.imagem.save("trabalho.jpg", ContentFile(imagem_bytes()), save=True)
    return foto


def _classe_do_body(html):
    return re.search(r'<body[^>]*class="([^"]*)"', html).group(1).split()


class HomeTests(HostsTestCase):
    def test_ca1_secoes_na_ordem_e_dados_do_rodape(self):
        resposta = self.site_get("/")
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "institucional/home.html")
        self.assertTemplateUsed(resposta, "site_base.html")
        html = resposta.content.decode()
        ids = ["inicio", "servicos", "portfolio", "sobre", "depoimentos", "contato", "rodape"]
        posicoes = [html.index(f'id="{secao}"') for secao in ids]
        self.assertEqual(posicoes, sorted(posicoes))
        self.assertContains(resposta, "Solicitar Orçamento")
        rodape = html[html.index('id="rodape"'):]
        for dado in ["(31) 9305-3178", "lojacreativemg@gmail.com", "instagram.com/loja.creativemg", "Ipatinga - MG"]:
            with self.subTest(dado=dado):
                self.assertIn(dado, rodape)

    def test_ca1_contexto_do_contrato(self):
        resposta = self.site_get("/")
        contexto = resposta.context
        for chave in ["config", "servicos", "categorias", "fotos", "depoimentos", "form", "whatsapp_url", "fundo_classe"]:
            with self.subTest(chave=chave):
                self.assertIn(chave, contexto)
        self.assertEqual(len(contexto["servicos"]), 5)
        self.assertEqual(set(contexto["servicos"][0]), {"titulo", "descricao", "icone"})
        for servico in contexto["servicos"]:
            self.assertContains(resposta, servico["titulo"])
        self.assertIsInstance(contexto["config"], ConfiguracaoSite)

    def test_ca2_botao_flutuante_do_whatsapp(self):
        resposta = self.site_get("/")
        esperado = "https://wa.me/553193053178?text=" + quote("Olá! Gostaria de solicitar um orçamento.", safe="")
        self.assertEqual(resposta.context["whatsapp_url"], esperado)
        self.assertContains(resposta, f'href="{esperado}"')
        self.assertNotIn(" ", esperado)

    def test_ca3_depoimento_inativo_nao_aparece(self):
        Depoimento.objects.all().delete()
        ativo = Depoimento.objects.create(nome="Paula", empresa="Padaria Central", texto="Ficou lindo.", ativo=True)
        inativo = Depoimento.objects.create(nome="Jorge", texto="Texto escondido.", ativo=False)
        resposta = self.site_get("/")
        self.assertEqual(list(resposta.context["depoimentos"]), [ativo])
        self.assertContains(resposta, "Ficou lindo.")
        self.assertNotContains(resposta, inativo.texto)

    def test_ca3_depoimentos_iniciais_entram_desativados(self):
        self.assertEqual(Depoimento.objects.count(), 3)
        self.assertFalse(Depoimento.objects.filter(ativo=True).exists())
        resposta = self.site_get("/")
        self.assertEqual(list(resposta.context["depoimentos"]), [])
        self.assertNotContains(resposta, "Carlos Silva")

    def test_ca4_head_com_title_description_og_e_favicon(self):
        resposta = self.site_get("/")
        self.assertContains(resposta, "<title>Creative Comunicação | Fachadas, ACM e Comunicação Visual</title>", html=False)
        self.assertContains(resposta, '<meta name="description"')
        for propriedade in ["og:title", "og:description", "og:type", "og:image", "og:url"]:
            with self.subTest(propriedade=propriedade):
                self.assertContains(resposta, f'property="{propriedade}"')
        self.assertContains(resposta, 'rel="icon"')

    def test_ca13_foto_nao_publicada_nao_aparece(self):
        publicada = _criar_foto(publicada=True)
        oculta = _criar_foto(publicada=False)
        resposta = self.site_get("/")
        self.assertIn(publicada, resposta.context["fotos"])
        self.assertNotIn(oculta, resposta.context["fotos"])
        self.assertContains(resposta, publicada.imagem.url)
        self.assertNotContains(resposta, oculta.imagem.url)

    def test_categorias_so_com_foto_publicada(self):
        fachadas = Categoria.objects.get(slug="letreiros-e-fachadas")
        adesivos = Categoria.objects.get(slug="adesivos-e-envelopamento")
        _criar_foto(categoria=fachadas)
        _criar_foto(categoria=fachadas)
        _criar_foto(publicada=False, categoria=adesivos)
        resposta = self.site_get("/")
        self.assertEqual(list(resposta.context["categorias"]), [fachadas])

    def test_fotos_ordenadas_e_sem_n_mais_1(self):
        fachadas = Categoria.objects.get(slug="letreiros-e-fachadas")
        segunda = _criar_foto(categoria=fachadas)
        primeira = _criar_foto(categoria=fachadas)
        primeira.ordem = 0
        primeira.save()
        segunda.ordem = 1
        segunda.save()
        resposta = self.site_get("/")
        fotos = resposta.context["fotos"]
        self.assertEqual(list(fotos), [primeira, segunda])
        with self.assertNumQueries(0):
            [foto.categoria.nome for foto in fotos]

    def test_ca15_modo_galeria_por_padrao(self):
        _criar_foto()
        resposta = self.site_get("/")
        self.assertEqual(resposta.context["config"].modo_fotos, "galeria")
        self.assertContains(resposta, 'data-modo="galeria"')

    def test_ca16_modo_carrossel(self):
        _criar_foto()
        config = ConfiguracaoSite.atual()
        config.modo_fotos = "carrossel"
        config.save()
        resposta = self.site_get("/")
        self.assertEqual(resposta.context["config"].modo_fotos, "carrossel")
        self.assertContains(resposta, 'data-modo="carrossel"')

    def test_ca17_banco_novo_usa_fundo_aurora(self):
        resposta = self.site_get("/")
        self.assertEqual(resposta.context["fundo_classe"], "fundo--aurora")
        self.assertIn("fundo--aurora", _classe_do_body(resposta.content.decode()))

    def test_ca17_atual_cria_configuracao_padrao_se_nao_existir(self):
        ConfiguracaoSite.objects.all().delete()
        config = ConfiguracaoSite.atual()
        self.assertEqual(config.pk, 1)
        self.assertEqual(config.fundo, "aurora")
        self.assertEqual(config.modo_fotos, "galeria")
        self.assertIn("fundo--aurora", _classe_do_body(self.site_get("/").content.decode()))

    def test_ca18_fundo_roxo_no_body(self):
        config = ConfiguracaoSite.atual()
        config.fundo = "roxo"
        config.save()
        self.assertIn("fundo--roxo", _classe_do_body(self.site_get("/").content.decode()))

    def test_home_aceita_so_get(self):
        self.assertEqual(self.site_post("/").status_code, 405)


class ConfiguracaoSiteTests(HostsTestCase):
    def test_dados_iniciais_com_contatos_reais(self):
        config = ConfiguracaoSite.atual()
        self.assertEqual(config.telefone, "(31) 9305-3178")
        self.assertEqual(config.whatsapp, "553193053178")
        self.assertEqual(config.email, "lojacreativemg@gmail.com")
        self.assertEqual(config.instagram, "https://www.instagram.com/loja.creativemg")
        self.assertEqual(config.cidade, "Ipatinga - MG")
        self.assertEqual(config.horario, "Seg - Sex: 8h às 18h")
        self.assertIsNone(config.anos_experiencia)

    def test_singleton_sempre_pk_1(self):
        nova = ConfiguracaoSite(telefone="1", whatsapp="1", email="a@b.com", cidade="x", horario="y")
        nova.save()
        self.assertEqual(ConfiguracaoSite.objects.count(), 1)
        self.assertEqual(nova.pk, 1)

    def test_telefone_href(self):
        self.assertEqual(ConfiguracaoSite.atual().telefone_href, "tel:+553193053178")
