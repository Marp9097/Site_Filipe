from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase

from config.testing import SENHA_TESTE


class CriarDonoTests(TestCase):
    def test_cria_staff_sem_superusuario_com_argumentos(self):
        saida = StringIO()
        call_command("criar_dono", usuario="creative", email="loja@example.com", senha=SENHA_TESTE, stdout=saida)
        dono = get_user_model().objects.get(username="creative")
        self.assertTrue(dono.is_staff)
        self.assertFalse(dono.is_superuser)
        self.assertTrue(dono.check_password(SENHA_TESTE))
        self.assertTrue(dono.password.startswith("argon2"))
        self.assertIn("criado", saida.getvalue())

    def test_pergunta_usuario_e_senha_quando_omitidos(self):
        with mock.patch("builtins.input", return_value="creative"), mock.patch(
            "apps.painel.management.commands.criar_dono.getpass", side_effect=[SENHA_TESTE, SENHA_TESTE]
        ):
            call_command("criar_dono", stdout=StringIO())
        self.assertTrue(get_user_model().objects.filter(username="creative", is_staff=True).exists())

    def test_senhas_diferentes_nao_criam_usuario(self):
        with mock.patch(
            "apps.painel.management.commands.criar_dono.getpass", side_effect=[SENHA_TESTE, "outra"]
        ), self.assertRaises(CommandError):
            call_command("criar_dono", usuario="creative", stdout=StringIO())
        self.assertFalse(get_user_model().objects.exists())

    def test_senha_fraca_e_recusada(self):
        with self.assertRaises(CommandError):
            call_command("criar_dono", usuario="creative", senha="123", stdout=StringIO())
        self.assertFalse(get_user_model().objects.exists())

    def test_usuario_existente_e_recusado(self):
        get_user_model().objects.create_user("creative", password=SENHA_TESTE)
        with self.assertRaises(CommandError):
            call_command("criar_dono", usuario="creative", senha=SENHA_TESTE, stdout=StringIO())
