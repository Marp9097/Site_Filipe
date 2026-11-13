from datetime import timedelta

from django.utils import timezone

from apps.institucional.models import Depoimento, MensagemContato
from config.testing import HostsTestCase


def _mensagem(nome, minutos_atras=0, **kwargs):
    mensagem = MensagemContato.objects.create(
        nome=nome,
        email=f"{nome.lower()}@example.com",
        telefone="(31) 98888-7777",
        servico="adesivos",
        mensagem="Preciso de adesivos.",
        **kwargs,
    )
    MensagemContato.objects.filter(pk=mensagem.pk).update(criada_em=timezone.now() - timedelta(minutes=minutos_atras))
    mensagem.refresh_from_db()
    return mensagem


class MensagensTests(HostsTestCase):
    def setUp(self):
        super().setUp()
        self.entrar_como_dono()

    def test_ca20_lista_mais_recentes_primeiro_com_destaque_nas_nao_lidas(self):
        antiga = _mensagem("Antiga", minutos_atras=60, lida=True)
        nova1 = _mensagem("Nova1", minutos_atras=30)
        nova2 = _mensagem("Nova2", minutos_atras=1)
        resposta = self.painel_get("/mensagens/")
        self.assertTemplateUsed(resposta, "painel/mensagens.html")
        self.assertEqual(list(resposta.context["mensagens"]), [nova2, nova1, antiga])
        self.assertEqual(resposta.context["page_obj"].paginator.count, 3)
        self.assertEqual(resposta.context["nao_lidas"], 2)
        self.assertContains(resposta, 'class="nao-lida"', count=2)

    def test_ca20_paginacao_de_20_em_20(self):
        for i in range(25):
            _mensagem(f"Pessoa{i}", minutos_atras=i)
        primeira = self.painel_get("/mensagens/")
        self.assertEqual(len(primeira.context["mensagens"]), 20)
        segunda = self.painel_get("/mensagens/?page=2")
        self.assertEqual(len(segunda.context["mensagens"]), 5)
        self.assertEqual(segunda.context["page_obj"].number, 2)
        invalida = self.painel_get("/mensagens/?page=abc")
        self.assertEqual(invalida.context["page_obj"].number, 1)

    def test_ca20_abrir_marca_como_lida_e_mostra_botoes_de_resposta(self):
        mensagem = _mensagem("Maria")
        resposta = self.painel_get(f"/mensagens/{mensagem.pk}/")
        self.assertTemplateUsed(resposta, "painel/mensagem.html")
        mensagem.refresh_from_db()
        self.assertTrue(mensagem.lida)
        self.assertEqual(resposta.context["mensagem"], mensagem)
        self.assertTrue(resposta.context["whatsapp_resposta_url"].startswith("https://wa.me/5531988887777?text="))
        self.assertTrue(resposta.context["mailto_url"].startswith("mailto:maria@example.com?subject="))
        self.assertContains(resposta, "Responder no WhatsApp")
        self.assertContains(resposta, "Responder por e-mail")

    def test_ca20_badge_de_nao_lidas_no_menu(self):
        _mensagem("Um")
        _mensagem("Dois")
        resposta = self.painel_get("/depoimentos/")
        self.assertEqual(resposta.context["nao_lidas"], 2)
        self.assertContains(resposta, 'class="badge"')

    def test_mensagem_inexistente_da_404(self):
        self.assertEqual(self.painel_get("/mensagens/999/").status_code, 404)


class DepoimentosTests(HostsTestCase):
    def setUp(self):
        super().setUp()
        self.entrar_como_dono()
        Depoimento.objects.all().delete()

    def _dados(self, **kwargs):
        dados = {"nome": "Paula", "empresa": "Padaria Central", "texto": "Ficou lindo!", "nota": 5, "ativo": "on", "ordem": 1}
        dados.update(kwargs)
        return {chave: valor for chave, valor in dados.items() if valor is not None}

    def test_ca21_criar_depoimento_aparece_no_site(self):
        resposta = self.painel_post("/depoimentos/", self._dados(), follow=True)
        self.assertContains(resposta, "Depoimento criado.")
        self.assertContains(self.site_get("/"), "Ficou lindo!")

    def test_ca21_editar_reflete_no_site(self):
        depoimento = Depoimento.objects.create(nome="Paula", texto="Texto antigo.")
        resposta = self.painel_get(f"/depoimentos/{depoimento.pk}/editar/")
        self.assertTemplateUsed(resposta, "painel/depoimento_form.html")
        self.assertEqual(resposta.context["depoimento"], depoimento)
        self.painel_post(f"/depoimentos/{depoimento.pk}/editar/", self._dados(texto="Texto novo."))
        site = self.site_get("/")
        self.assertContains(site, "Texto novo.")
        self.assertNotContains(site, "Texto antigo.")

    def test_ca21_desativar_tira_do_site(self):
        depoimento = Depoimento.objects.create(nome="Paula", texto="Vai sumir.")
        self.painel_post(f"/depoimentos/{depoimento.pk}/editar/", self._dados(texto="Vai sumir.", ativo=None))
        depoimento.refresh_from_db()
        self.assertFalse(depoimento.ativo)
        self.assertNotContains(self.site_get("/"), "Vai sumir.")

    def test_ca21_excluir_tira_do_site(self):
        depoimento = Depoimento.objects.create(nome="Paula", texto="Excluído.")
        resposta = self.painel_post(f"/depoimentos/{depoimento.pk}/excluir/")
        self.assertRedirects(resposta, "/depoimentos/", fetch_redirect_response=False)
        self.assertFalse(Depoimento.objects.exists())
        self.assertNotContains(self.site_get("/"), "Excluído.")

    def test_ca21_ordem_definida_no_painel(self):
        self.painel_post("/depoimentos/", self._dados(nome="Segundo", texto="B", ordem=2))
        self.painel_post("/depoimentos/", self._dados(nome="Primeiro", texto="A", ordem=1))
        nomes = [d.nome for d in self.site_get("/").context["depoimentos"]]
        self.assertEqual(nomes, ["Primeiro", "Segundo"])

    def test_lista_mostra_ativos_e_inativos(self):
        Depoimento.objects.create(nome="Ativo", texto="a", ativo=True)
        Depoimento.objects.create(nome="Inativo", texto="b", ativo=False)
        resposta = self.painel_get("/depoimentos/")
        self.assertEqual(resposta.context["depoimentos"].count(), 2)
        self.assertIn("form", resposta.context)

    def test_texto_acima_de_600_e_nota_fora_de_1_a_5_sao_rejeitados(self):
        resposta = self.painel_post("/depoimentos/", self._dados(texto="a" * 601, nota=9))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(set(resposta.context["form"].errors), {"texto", "nota"})
        self.assertFalse(Depoimento.objects.exists())

    def test_excluir_exige_post(self):
        depoimento = Depoimento.objects.create(nome="Paula", texto="x")
        self.assertEqual(self.painel_get(f"/depoimentos/{depoimento.pk}/excluir/").status_code, 405)
