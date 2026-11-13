from django.db import migrations

CATEGORIAS = [
    ("Letreiros e Fachadas", "letreiros-e-fachadas"),
    ("Adesivos e Envelopamento", "adesivos-e-envelopamento"),
    ("Personalização", "personalizacao"),
    ("Estruturas Metálicas", "estruturas-metalicas"),
    ("Impressão Digital", "impressao-digital"),
]


def criar_categorias(apps, schema_editor):
    Categoria = apps.get_model("portfolio", "Categoria")
    for ordem, (nome, slug) in enumerate(CATEGORIAS, start=1):
        Categoria.objects.get_or_create(slug=slug, defaults={"nome": nome, "ordem": ordem})


def remover_categorias(apps, schema_editor):
    Categoria = apps.get_model("portfolio", "Categoria")
    Categoria.objects.filter(slug__in=[slug for _nome, slug in CATEGORIAS], fotos__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("portfolio", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(criar_categorias, remover_categorias),
    ]
