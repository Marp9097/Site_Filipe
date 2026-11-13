from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Cria o usuário do dono para o painel (is_staff=True, sem superusuário)."

    def add_arguments(self, parser):
        parser.add_argument("--usuario", help="Nome de usuário para entrar no painel.")
        parser.add_argument("--email", default="", help="E-mail do dono (opcional).")
        parser.add_argument(
            "--senha",
            help="Senha. Se omitida, será perguntada sem aparecer na tela (recomendado).",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        usuario = (options["usuario"] or input("Usuário: ")).strip()
        if not usuario:
            raise CommandError("Informe o nome de usuário.")
        if User.objects.filter(username=usuario).exists():
            raise CommandError(f"O usuário “{usuario}” já existe.")

        senha = options["senha"]
        if senha is None:
            senha = getpass("Senha: ")
            if senha != getpass("Repita a senha: "):
                raise CommandError("As senhas não conferem.")

        candidato = User(username=usuario, email=options["email"])
        try:
            validate_password(senha, user=candidato)
        except ValidationError as erro:
            raise CommandError(" ".join(erro.messages)) from erro

        User.objects.create_user(
            username=usuario,
            email=options["email"],
            password=senha,
            is_staff=True,
            is_superuser=False,
        )
        self.stdout.write(self.style.SUCCESS(f"Usuário “{usuario}” criado. Ele já pode entrar no painel."))
