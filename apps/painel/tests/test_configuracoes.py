import re

from apps.institucional.models import ConfiguracaoSite
from config.testing import HostsTestCase


def _dados(**kwargs):
    dados = {
        "fundo": "aurora",
        "modo_fotos": "galeria",
        "telefone": "(31) 9305-3178",
        "whatsapp": "553193053178",
        "email": "lojacreativemg@gmail.com",
        "instagram": "https://www.instagram.com/loja.creativemg",
        "cidade": "Ipatinga - MG",
        "horario": "Seg - Sex: 8h às 18h",
        "anos_experiencia": "",
    }
    dados.update(kwargs)
    return dados


class ConfiguracoesTests(HostsTestCase):
    def setUp(self):
        super().setUp()
        self.entrar_como_dono()

    def test_contexto_da_tela(self):
        resposta = self.painel_get("/configuracoes/")
        self.assertTemplateUsed(resposta, "painel/configuracoes.html")
        self.assertEqual(
            resposta.context["opcoes_fundo"],
            [
                {"valor": "aurora", "rotulo": "Estilo Lovable (padrão)", "classe": "fundo--aurora"},
                {"valor": "roxo", "rotulo": "Roxo Creative", "classe": "fundo--roxo"},
                {"valor": "claro", "rotulo": "Claro liso", "classe": "fundo--claro"},
                {"valor": "escuro", "rotulo": "Escuro liso", "classe": "fundo--escuro"},
            ],
        )
        self.assertEqual(
            resposta.context["opcoes_modo"],
            [{"valor": "galeria", "rotulo": "Galeria"}, {"valor": "carrossel", "rotulo": "Carrossel"}],
        )
        form = resposta.context["form"]
        self.assertEqual(form.fields["fundo"].widget.__class__.__name__, "RadioSelect")
        self.assertEqual(form.fields["modo_fotos"].widget.__class__.__name__, "RadioSelect")

    def test_ca18_cada_opcao_de_fundo_tem_previa(self):
        resposta = self.painel_get("/configuracoes/")
        for classe in ["fundo--aurora", "fundo--roxo", "fundo--claro", "fundo--escuro"]:
            with self.subTest(classe=classe):
                self.assertContains(resposta, f"previa {classe}")

    def test_ca16_trocar_para_carrossel_reflete_no_site(self):
        resposta = self.painel_post("/configuracoes/", _dados(modo_fotos="carrossel"), follow=True)
        self.assertContains(resposta, "Configurações salvas.")
        self.assertEqual(ConfiguracaoSite.atual().modo_fotos, "carrossel")
        self.assertEqual(self.site_get("/").context["config"].modo_fotos, "carrossel")

    def test_ca15_voltar_para_galeria(self):
        self.painel_post("/configuracoes/", _dados(modo_fotos="carrossel"))
        self.painel_post("/configuracoes/", _dados(modo_fotos="galeria"))
        self.assertEqual(self.site_get("/").context["config"].modo_fotos, "galeria")

    def test_ca18_escolher_roxo_muda_classe_do_body(self):
        self.painel_post("/configuracoes/", _dados(fundo="roxo"))
        html = self.site_get("/").content.decode()
        classes = re.search(r'<body[^>]*class="([^"]*)"', html).group(1).split()
        self.assertIn("fundo--roxo", classes)
        self.assertNotIn("fundo--aurora", classes)

    def test_ca19_novos_contatos_aparecem_no_site(self):
        novos = _dados(
            telefone="(31) 3822-1000",
            whatsapp="+55 (31) 99876-5432",
            email="contato@creative.com.br",
            instagram="https://www.instagram.com/creative.nova",
        )
        self.painel_post("/configuracoes/", novos)
        config = ConfiguracaoSite.atual()
        self.assertEqual(config.whatsapp, "5531998765432")
        resposta = self.site_get("/")
        html = resposta.content.decode()
        rodape = html[html.index('id="rodape"'):]
        for dado in ["(31) 3822-1000", "contato@creative.com.br", "instagram.com/creative.nova"]:
            with self.subTest(dado=dado):
                self.assertIn(dado, rodape)
        self.assertContains(resposta, "https://wa.me/5531998765432?text=")
        self.assertTrue(resposta.context["whatsapp_url"].startswith("https://wa.me/5531998765432?"))

    def test_whatsapp_invalido_mostra_erro(self):
        resposta = self.painel_post("/configuracoes/", _dados(whatsapp="9305-3178"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Informe o WhatsApp com DDI e DDD, ex.: 553193053178.", resposta.context["form"].errors["whatsapp"])
        self.assertEqual(ConfiguracaoSite.atual().whatsapp, "553193053178")

    def test_fundo_fora_das_opcoes_e_rejeitado(self):
        resposta = self.painel_post("/configuracoes/", _dados(fundo="neon"))
        self.assertIn("fundo", resposta.context["form"].errors)
        self.assertEqual(ConfiguracaoSite.atual().fundo, "aurora")

    def test_anos_de_experiencia_aparece_quando_preenchido(self):
        self.assertNotContains(self.site_get("/"), "Anos de Experiência")
        self.painel_post("/configuracoes/", _dados(anos_experiencia="12"))
        self.assertContains(self.site_get("/"), "Anos de Experiência")
