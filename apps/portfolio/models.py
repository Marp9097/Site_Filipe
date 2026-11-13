from django.db import models
from django.utils.text import slugify


class Categoria(models.Model):
    nome = models.CharField("nome", max_length=60, unique=True)
    slug = models.SlugField("slug", max_length=60, unique=True)
    ordem = models.PositiveSmallIntegerField("ordem", default=0)

    class Meta:
        ordering = ["ordem", "nome"]
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)


class Foto(models.Model):
    imagem = models.ImageField("imagem", upload_to="portfolio/%Y/%m/")
    titulo = models.CharField("título", max_length=120, blank=True)
    publicada = models.BooleanField("publicada", default=True)
    ordem = models.PositiveIntegerField("ordem", default=0)
    criada_em = models.DateTimeField("criada em", auto_now_add=True)
    categoria = models.ForeignKey(
        Categoria,
        verbose_name="categoria",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="fotos",
    )

    class Meta:
        ordering = ["ordem", "-criada_em"]
        verbose_name = "foto"
        verbose_name_plural = "fotos"

    def __str__(self):
        return self.titulo or self.imagem.name

    @property
    def texto_alternativo(self):
        if self.titulo:
            return self.titulo
        if self.categoria_id:
            return f"{self.categoria.nome}: trabalho da Creative Comunicação"
        return "Trabalho da Creative Comunicação"
