from apps.institucional.models import MensagemContato
from config.testing import HostsTestCase

DADOS_VALIDOS = {
    "nome": "Maria Souza",
    "email": "maria@example.com",
    "telefone": "(31) 98888-7777",
    "servico": "fachadas",
    "mensagem": "Quero orçar uma fachada em ACM.",
}


class ContatoTests(HostsTestCase):
    def test_ca5_envio_valido_cria_mensagem_e_redireciona(self):
        resposta = self.site_post("/contato/", DADOS_VALIDOS)
        self.assertRedirects(resposta, "/#contato", fetch_redirect_response=False)
        mensagem = MensagemContato.objects.get()
        self.assertFalse(mensagem.lida)
        self.assertEqual(mensagem.nome, "Maria Souza")
        self.assertEqual(mensagem.servico, "fachadas")

    def test_ca5_mensagem_de_sucesso_aparece_na_home(self):
        resposta = self.site_post("/contato/", DADOS_VALIDOS, follow=True)
        self.assertContains(resposta, "Mensagem enviada! Em breve entramos em contato.")

    def test_ca6_email_invalido_nao_salva_e_mostra_erro_preservando_dados(self):
        dados = {**DADOS_VALIDOS, "email": "maria-sem-arroba"}
        resposta = self.site_post("/contato/", dados)
        self.assertEqual(resposta.status_code, 200)
        self.assertTemplateUsed(resposta, "institucional/home.html")
        self.assertFalse(MensagemContato.objects.exists())
        form = resposta.context["form"]
        self.assertIn("Informe um endereço de email válido.", form.errors["email"])
        self.assertContains(resposta, 'id="erro-email"')
        self.assertContains(resposta, 'value="Maria Souza"')
        self.assertContains(resposta, "Quero orçar uma fachada em ACM.")

    def test_ca6_mensagem_vazia_nao_salva(self):
        resposta = self.site_post("/contato/", {**DADOS_VALIDOS, "mensagem": "   "})
        self.assertFalse(MensagemContato.objects.exists())
        self.assertIn("Este campo é obrigatório.", resposta.context["form"].errors["mensagem"])
        self.assertContains(resposta, 'id="erro-mensagem"')

    def test_ca6_erro_renderiza_com_o_mesmo_contexto_da_home(self):
        resposta = self.site_post("/contato/", {})
        for chave in ["config", "servicos", "categorias", "fotos", "depoimentos", "form", "whatsapp_url"]:
            with self.subTest(chave=chave):
                self.assertIn(chave, resposta.context)
        self.assertEqual(set(resposta.context["form"].errors), {"nome", "email", "telefone", "servico", "mensagem"})

    def test_mensagem_acima_de_2000_caracteres_e_rejeitada(self):
        resposta = self.site_post("/contato/", {**DADOS_VALIDOS, "mensagem": "a" * 2001})
        self.assertFalse(MensagemContato.objects.exists())
        self.assertIn("mensagem", resposta.context["form"].errors)

    def test_telefone_sem_ddd_e_rejeitado(self):
        resposta = self.site_post("/contato/", {**DADOS_VALIDOS, "telefone": "9999-0000"})
        self.assertFalse(MensagemContato.objects.exists())
        self.assertIn("Informe o telefone com DDD, ex.: (31) 99999-9999.", resposta.context["form"].errors["telefone"])

    def test_servico_invalido_e_rejeitado(self):
        resposta = self.site_post("/contato/", {**DADOS_VALIDOS, "servico": "hackear"})
        self.assertFalse(MensagemContato.objects.exists())
        self.assertIn("servico", resposta.context["form"].errors)

    def test_contato_aceita_so_post(self):
        self.assertEqual(self.site_get("/contato/").status_code, 405)

    def test_form_tem_csrf_token(self):
        self.assertContains(self.site_get("/"), 'name="csrfmiddlewaretoken"')
