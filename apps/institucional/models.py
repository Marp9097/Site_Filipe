from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

somente_digitos = RegexValidator(r"^\d+$", "Use só números, com DDI e DDD (ex.: 553193053178).")


class ConfiguracaoSite(models.Model):
    class Fundo(models.TextChoices):
        AURORA = "aurora", "Estilo Lovable (padrão)"
        ROXO = "roxo", "Roxo Creative"
        CLARO = "claro", "Claro liso"
        ESCURO = "escuro", "Escuro liso"

    class ModoFotos(models.TextChoices):
        GALERIA = "galeria", "Galeria"
        CARROSSEL = "carrossel", "Carrossel"

    fundo = models.CharField("fundo do site", max_length=20, choices=Fundo.choices, default=Fundo.AURORA)
    modo_fotos = models.CharField(
        "exibição das fotos", max_length=20, choices=ModoFotos.choices, default=ModoFotos.GALERIA
    )
    telefone = models.CharField("telefone", max_length=20)
    whatsapp = models.CharField("WhatsApp", max_length=15, validators=[somente_digitos])
    email = models.EmailField("e-mail")
    instagram = models.URLField("Instagram", blank=True)
    cidade = models.CharField("cidade", max_length=60)
    horario = models.CharField("horário de atendimento", max_length=60)
    anos_experiencia = models.PositiveSmallIntegerField("anos de experiência", null=True, blank=True)
    atualizado_em = models.DateTimeField("atualizado em", auto_now=True)

    class Meta:
        verbose_name = "configuração do site"
        verbose_name_plural = "configuração do site"

    def __str__(self):
        return "Configuração do site"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def atual(cls):
        config, _criada = cls.objects.get_or_create(pk=1)
        return config

    @property
    def fundo_classe(self):
        return f"fundo--{self.fundo}"

    @property
    def telefone_href(self):
        digitos = "".join(c for c in self.telefone if c.isdigit())
        if len(digitos) in (10, 11):
            digitos = f"55{digitos}"
        return f"tel:+{digitos}" if digitos else ""


class Depoimento(models.Model):
    nome = models.CharField("nome", max_length=80)
    empresa = models.CharField("empresa", max_length=80, blank=True)
    texto = models.TextField("depoimento")
    nota = models.PositiveSmallIntegerField(
        "nota", default=5, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    ativo = models.BooleanField("ativo (aparece no site)", default=True)
    ordem = models.PositiveSmallIntegerField("ordem", default=0)

    class Meta:
        ordering = ["ordem", "id"]
        verbose_name = "depoimento"
        verbose_name_plural = "depoimentos"

    def __str__(self):
        return f"{self.nome} ({self.empresa})" if self.empresa else self.nome


class MensagemContato(models.Model):
    class Servico(models.TextChoices):
        FACHADAS = "fachadas", "Letreiros e Fachadas"
        ADESIVOS = "adesivos", "Adesivos e Envelopamento"
        PERSONALIZACAO = "personalizacao", "Personalização"
        ESTRUTURAS = "estruturas", "Estruturas Metálicas"
        IMPRESSAO = "impressao", "Impressão Digital"
        OUTRO = "outro", "Outro"

    nome = models.CharField("nome", max_length=100)
    email = models.EmailField("e-mail")
    telefone = models.CharField("telefone", max_length=20)
    servico = models.CharField("serviço de interesse", max_length=30, choices=Servico.choices)
    mensagem = models.TextField("mensagem")
    lida = models.BooleanField("lida", default=False)
    criada_em = models.DateTimeField("recebida em", auto_now_add=True)

    class Meta:
        ordering = ["-criada_em", "-id"]
        verbose_name = "mensagem de contato"
        verbose_name_plural = "mensagens de contato"

    def __str__(self):
        return f"{self.nome} ({self.get_servico_display()})"
