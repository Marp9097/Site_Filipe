from django.contrib.auth import get_user_model

from config.testing import SENHA_TESTE, HostsTestCase

ROTAS_DO_PAINEL = [
    "/entrar/",
    "/sair/",
    "/fotos/",
    "/fotos/1/editar/",
    "/categorias/",
    "/configuracoes/",
    "/depoimentos/",
    "/mensagens/",
    "/mensagens/1/",
    "/django-admin/",
    "/django-admin/login/",
]


class RoteamentoPorHostTests(HostsTestCase):
    def test_ca7_painel_deslogado_redireciona_para_entrar(self):
        resposta = self.painel_get("/")
        self.assertRedirects(resposta, "/entrar/?next=/", fetch_redirect_response=False)

    def test_ca7_painel_deslogado_em_outra_tela_preserva_next(self):
        resposta = self.painel_get("/fotos/")
        self.assertRedirects(resposta, "/entrar/?next=/fotos/", fetch_redirect_response=False)

    def test_ca7_tela_de_entrar_abre_no_painel(self):
        resposta = self.painel_get("/entrar/")
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "painel/entrar.html")

    def test_ca8_rotas_do_painel_dao_404_no_host_do_site(self):
        for url in ["/entrar/", "/fotos/", "/configuracoes/", "/django-admin/"]:
            with self.subTest(url=url):
                self.assertEqual(self.site_get(url).status_code, 404)

    def test_cap1_nenhuma_rota_do_painel_existe_no_host_do_site(self):
        for url in ROTAS_DO_PAINEL:
            with self.subTest(url=url):
                self.assertEqual(self.site_get(url).status_code, 404)

    def test_cap1_staff_logado_tambem_recebe_404_no_host_do_site(self):
        self.entrar_como_dono()
        for url in ["/fotos/", "/configuracoes/", "/mensagens/"]:
            with self.subTest(url=url):
                self.assertEqual(self.site_get(url).status_code, 404)

    def test_host_com_porta_tambem_e_roteado_para_o_painel(self):
        resposta = self.client.get("/", HTTP_HOST="painel.localhost:8000")
        self.assertRedirects(resposta, "/entrar/?next=/", fetch_redirect_response=False)

    def test_site_na_raiz_do_host_do_site(self):
        resposta = self.site_get("/")
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "institucional/home.html")

    def test_cap5_sem_rota_de_cadastro_em_nenhum_host(self):
        for url in ["/register/", "/cadastro/", "/admin/register/", "/admin/register", "/signup/"]:
            with self.subTest(url=url):
                self.assertEqual(self.site_get(url).status_code, 404)
                self.assertEqual(self.painel_get(url).status_code, 404)


class DjangoAdminTests(HostsTestCase):
    def test_django_admin_existe_so_no_painel(self):
        resposta = self.painel_get("/django-admin/")
        self.assertRedirects(resposta, "/django-admin/login/?next=/django-admin/", fetch_redirect_response=False)

    def test_django_admin_libera_superusuario(self):
        admin = get_user_model().objects.create_superuser("marcos", "marcos@example.com", SENHA_TESTE)
        self.client.force_login(admin)
        self.assertEqual(self.painel_get("/django-admin/").status_code, 200)

    def test_django_admin_bloqueia_dono_que_nao_e_superusuario(self):
        self.entrar_como_dono()
        resposta = self.painel_get("/django-admin/")
        self.assertRedirects(resposta, "/django-admin/login/?next=/django-admin/", fetch_redirect_response=False)

