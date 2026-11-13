from django.db import migrations

CONFIGURACAO = {
    "fundo": "aurora",
    "modo_fotos": "galeria",
    "telefone": "(31) 9305-3178",
    "whatsapp": "553193053178",
    "email": "lojacreativemg@gmail.com",
    "instagram": "https://www.instagram.com/loja.creativemg",
    "cidade": "Ipatinga - MG",
    "horario": "Seg - Sex: 8h às 18h",
    "anos_experiencia": None,
}

# Depoimentos do site atual. Parecem conteúdo de exemplo: entram desativados até o cliente confirmar.
DEPOIMENTOS = [
    {
        "nome": "Carlos Silva",
        "empresa": "Restaurante Sabor & Arte",
        "texto": (
            "A Creative Comunicação superou todas as nossas expectativas! A fachada do restaurante ficou "
            "incrível e atraiu muito mais clientes. Profissionais excelentes e atendimento impecável."
        ),
    },
    {
        "nome": "Ana Rodrigues",
        "empresa": "Clínica Bem Estar",
        "texto": (
            "Contratamos para fazer toda a sinalização da clínica e o resultado foi perfeito. Material de "
            "qualidade, instalação rápida e preço justo. Recomendo a todos!"
        ),
    },
    {
        "nome": "Fernanda Costa",
        "empresa": "Boutique Fashion",
        "texto": (
            "Fizeram o letreiro e a decoração da vitrine da nossa loja. O trabalho artístico é de altíssima "
            "qualidade. Nossa loja nunca esteve tão bonita! Agradeço toda a dedicação."
        ),
    },
]


def criar_dados(apps, schema_editor):
    ConfiguracaoSite = apps.get_model("institucional", "ConfiguracaoSite")
    Depoimento = apps.get_model("institucional", "Depoimento")
    ConfiguracaoSite.objects.update_or_create(pk=1, defaults=CONFIGURACAO)
    for ordem, dados in enumerate(DEPOIMENTOS, start=1):
        Depoimento.objects.get_or_create(
            nome=dados["nome"],
            empresa=dados["empresa"],
            defaults={"texto": dados["texto"], "nota": 5, "ativo": False, "ordem": ordem},
        )


def remover_dados(apps, schema_editor):
    Depoimento = apps.get_model("institucional", "Depoimento")
    for dados in DEPOIMENTOS:
        Depoimento.objects.filter(nome=dados["nome"], empresa=dados["empresa"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("institucional", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(criar_dados, remover_dados),
    ]
