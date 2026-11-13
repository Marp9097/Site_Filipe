from django.test import SimpleTestCase

from apps.institucional import services
from apps.institucional.models import MensagemContato


class WhatsappTests(SimpleTestCase):
    def test_ca2_url_com_texto_codificado(self):
        self.assertEqual(
            services.whatsapp_url("553193053178", "Olá! Gostaria de solicitar um orçamento."),
            "https://wa.me/553193053178?text=Ol%C3%A1%21%20Gostaria%20de%20solicitar%20um%20or%C3%A7amento.",
        )

    def test_url_ignora_caracteres_nao_numericos(self):
        self.assertTrue(services.whatsapp_url("+55 (31) 9305-3178").startswith("https://wa.me/553193053178?"))

    def test_url_vazia_sem_numero(self):
        self.assertEqual(services.whatsapp_url(""), "")

    def test_numero_brasil_a_partir_do_telefone_digitado(self):
        self.assertEqual(services.numero_whatsapp_brasil("(31) 98888-7777"), "5531988887777")
        self.assertEqual(services.numero_whatsapp_brasil("(31) 3333-4444"), "553133334444")
        self.assertEqual(services.numero_whatsapp_brasil("+55 31 98888-7777"), "5531988887777")
        self.assertEqual(services.numero_whatsapp_brasil("123"), "")

    def test_links_de_resposta(self):
        mensagem = MensagemContato(nome="Maria", email="maria@example.com", telefone="(31) 98888-7777")
        self.assertTrue(services.resposta_whatsapp_url(mensagem).startswith("https://wa.me/5531988887777?text=Ol%C3%A1%2C%20Maria"))
        self.assertEqual(
            services.mailto_url(mensagem),
            "mailto:maria@example.com?subject=Re%3A%20Seu%20contato%20pelo%20site%20da%20Creative%20Comunica%C3%A7%C3%A3o",
        )

    def test_sem_whatsapp_de_resposta_se_telefone_invalido(self):
        mensagem = MensagemContato(nome="Maria", email="maria@example.com", telefone="123")
        self.assertEqual(services.resposta_whatsapp_url(mensagem), "")

    def test_servicos_sao_os_5_do_site_atual(self):
        self.assertEqual(
            [s["titulo"] for s in services.SERVICOS],
            ["Letreiros e Fachadas", "Adesivos e Envelopamento", "Personalização", "Estruturas Metálicas", "Impressão Digital"],
        )
