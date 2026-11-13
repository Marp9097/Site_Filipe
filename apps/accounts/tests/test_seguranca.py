from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from apps.accounts.models import User

IGNORADOS = {".venv", ".git", "media", "staticfiles", "__pycache__"}
ARQUIVOS_FORA_DO_GIT = {".env", "db.sqlite3"}


def _arquivos_versionaveis(raiz):
    for caminho in raiz.rglob("*"):
        if not caminho.is_file():
            continue
        relativo = caminho.relative_to(raiz)
        if IGNORADOS.intersection(relativo.parts) or relativo.name in ARQUIVOS_FORA_DO_GIT:
            continue
        yield caminho


class UsuarioCustomizadoTests(TestCase):
    def test_auth_user_model_e_o_customizado(self):
        self.assertEqual(settings.AUTH_USER_MODEL, "accounts.User")
        self.assertIs(get_user_model(), User)

    def test_senha_com_argon2(self):
        usuario = User.objects.create_user("x", password="Senha-Forte-123")
        self.assertTrue(usuario.password.startswith("argon2$"))


class SegredosTests(SimpleTestCase):
    def test_cap4_secret_key_nao_aparece_em_arquivo_versionavel(self):
        chave = settings.SECRET_KEY
        self.assertGreaterEqual(len(chave), 32)
        for arquivo in _arquivos_versionaveis(Path(settings.BASE_DIR)):
            with self.subTest(arquivo=str(arquivo)):
                self.assertNotIn(chave.encode(), arquivo.read_bytes())

    def test_cap4_gitignore_protege_env_banco_e_midia(self):
        gitignore = (Path(settings.BASE_DIR) / ".gitignore").read_text(encoding="utf-8").split()
        for entrada in [".env", ".venv/", "db.sqlite3", "__pycache__/", "media/", "staticfiles/"]:
            with self.subTest(entrada=entrada):
                self.assertIn(entrada, gitignore)

    def test_cap4_env_example_so_tem_placeholders(self):
        exemplo = (Path(settings.BASE_DIR) / ".env.example").read_text(encoding="utf-8")
        self.assertIn("SECRET_KEY=", exemplo)
        self.assertNotIn(settings.SECRET_KEY, exemplo)

    def test_settings_essenciais(self):
        self.assertEqual(settings.LANGUAGE_CODE, "pt-br")
        self.assertEqual(settings.TIME_ZONE, "America/Sao_Paulo")
        self.assertEqual(settings.LOGIN_URL, "/entrar/")
        self.assertIsNone(settings.SESSION_COOKIE_DOMAIN)
        self.assertEqual(settings.PASSWORD_HASHERS[0], "django.contrib.auth.hashers.Argon2PasswordHasher")
