from django.contrib.auth import get_user_model
from django.test import Client

from apps.institucional.models import Depoimento, MensagemContato
from apps.portfolio.models import Categoria
from config.testing import PAINEL, SENHA_TESTE, SITE, HostsTestCase


def _mensagem(**kwargs):
    dados = {
        "nome": "Cliente",
        "email": "cliente@example.com",
        "telefone": "(31) 99999-0000",
        "servico": "fachadas",
        "mensagem": "Quero um orçamento.",
        **kwargs,
    }
    return MensagemContato.objects.create(**dados)


class PermissaoStaffTests(HostsTestCase):
    def setUp(self):
        super().setUp()
        self.mensagem = _mensagem()
        self.depoimento = Depoimento.objects.create(nome="Ana", texto="Ótimo")
        self.categoria = Categoria.objects.create(nome="Teste")
        comum = get_user_model().objects.create_user("visitante", password=SENHA_TESTE)
        self.client.force_login(comum)

    def test_ca9_logado_sem_staff_recebe_403_em_todas_as_telas_get(self):
        for url in [
            "/",
            "/fotos/",
            "/fotos/999/editar/",
            "/categorias/",
            "/configuracoes/",
            "/depoimentos/",
            f"/depoimentos/{self.depoimento.pk}/editar/",
            "/mensagens/",
            f"/mensagens/{self.mensagem.pk}/",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.painel_get(url).status_code, 403)

    def test_ca9_logado_sem_staff_recebe_403_nos_posts(self):
        for url in [
            "/fotos/",
            "/fotos/999/excluir/",
            f"/categorias/{self.categoria.pk}/excluir/",
            "/configuracoes/",
            "/depoimentos/",
            f"/depoimentos/{self.depoimento.pk}/excluir/",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.painel_post(url).status_code, 403)
        self.assertTrue(Categoria.objects.filter(pk=self.categoria.pk).exists())
        self.assertTrue(Depoimento.objects.filter(pk=self.depoimento.pk).exists())

    def test_ca9_nao_marca_mensagem_como_lida_para_nao_staff(self):
        self.painel_get(f"/mensagens/{self.mensagem.pk}/")
        self.mensagem.refresh_from_db()
        self.assertFalse(self.mensagem.lida)


class EntrarTests(HostsTestCase):
    def test_ca10_login_correto_mostra_inicio_com_totais(self):
        self.criar_dono()
        _mensagem()
        _mensagem(lida=True)
        resposta = self.painel_post("/entrar/", {"username": "dono", "password": SENHA_TESTE}, follow=True)
        self.assertEqual(resposta.redirect_chain[-1], ("/", 302))
        self.assertTemplateUsed(resposta, "painel/inicio.html")
        self.assertEqual(resposta.context["total_fotos"], 0)
        self.assertEqual(resposta.context["nao_lidas"], 1)
        self.assertIn("total_publicadas", resposta.context)
        self.assertEqual(len(resposta.context["ultimas_mensagens"]), 2)
        self.assertEqual(resposta.context["config"].pk, 1)

    def test_ca10_login_respeita_next(self):
        self.criar_dono()
        resposta = self.painel_post("/entrar/?next=/fotos/", {"username": "dono", "password": SENHA_TESTE, "next": "/fotos/"})
        self.assertRedirects(resposta, "/fotos/", fetch_redirect_response=False)

    def test_ca10_senha_errada_mostra_mensagem(self):
        self.criar_dono()
        resposta = self.painel_post("/entrar/", {"username": "dono", "password": "errada"})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Usuário ou senha incorretos.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_ca10_usuario_inexistente_mostra_mesma_mensagem(self):
        resposta = self.painel_post("/entrar/", {"username": "ninguem", "password": "x"})
        self.assertContains(resposta, "Usuário ou senha incorretos.")

    def test_inicio_limita_ultimas_mensagens_a_5(self):
        self.entrar_como_dono()
        for i in range(7):
            _mensagem(nome=f"Cliente {i}")
        resposta = self.painel_get("/")
        self.assertEqual(len(resposta.context["ultimas_mensagens"]), 5)
        self.assertEqual(resposta.context["ultimas_mensagens"][0].nome, "Cliente 6")

    def test_sair_por_post_redireciona_para_entrar(self):
        self.entrar_como_dono()
        resposta = self.painel_post("/sair/")
        self.assertRedirects(resposta, "/entrar/", fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_sair_por_get_nao_e_permitido(self):
        self.entrar_como_dono()
        self.assertEqual(self.painel_get("/sair/").status_code, 405)

    def test_sessao_do_painel_nao_vale_no_site(self):
        self.criar_dono()
        resposta = self.painel_post("/entrar/", {"username": "dono", "password": SENHA_TESTE})
        cookie = resposta.cookies["sessionid"]
        self.assertEqual(cookie["domain"], "")


class CsrfTests(HostsTestCase):
    def setUp(self):
        super().setUp()
        self.csrf_client = Client(enforce_csrf_checks=True)

    def test_cap2_post_sem_csrf_no_painel_retorna_403(self):
        dono = self.criar_dono()
        self.csrf_client.force_login(dono)
        depoimento = Depoimento.objects.create(nome="Ana", texto="Ótimo")
        for url in ["/configuracoes/", "/depoimentos/", f"/depoimentos/{depoimento.pk}/excluir/", "/fotos/", "/sair/"]:
            with self.subTest(url=url):
                resposta = self.csrf_client.post(url, {}, HTTP_HOST=PAINEL)
                self.assertEqual(resposta.status_code, 403)
        self.assertTrue(Depoimento.objects.filter(pk=depoimento.pk).exists())

    def test_cap2_login_sem_csrf_retorna_403(self):
        self.criar_dono()
        resposta = self.csrf_client.post("/entrar/", {"username": "dono", "password": SENHA_TESTE}, HTTP_HOST=PAINEL)
        self.assertEqual(resposta.status_code, 403)

    def test_cap2_post_sem_csrf_no_contato_retorna_403(self):
        dados = {
            "nome": "Maria",
            "email": "maria@example.com",
            "telefone": "(31) 98888-7777",
            "servico": "fachadas",
            "mensagem": "Olá",
        }
        resposta = self.csrf_client.post("/contato/", dados, HTTP_HOST=SITE)
        self.assertEqual(resposta.status_code, 403)
        self.assertFalse(MensagemContato.objects.exists())
