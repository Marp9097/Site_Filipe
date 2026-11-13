from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageOps

from .models import Foto

FORMATOS_ACEITOS = {"JPEG", "PNG", "WEBP"}
QUALIDADE = 85


def _mb(tamanho):
    return f"{tamanho / (1024 * 1024):.1f}".replace(".", ",")


def validar_arquivos(arquivos):
    """Valida quantidade, tamanho e CONTEÚDO (Pillow) dos arquivos. Levanta ValidationError com todos os erros."""
    if not arquivos:
        raise ValidationError("Selecione ao menos uma foto.")
    limite_qtd = settings.UPLOAD_MAX_ARQUIVOS
    if len(arquivos) > limite_qtd:
        raise ValidationError(f"Envie no máximo {limite_qtd} fotos por vez (você selecionou {len(arquivos)}).")

    limite_bytes = settings.UPLOAD_MAX_BYTES
    erros = []
    for arquivo in arquivos:
        nome = arquivo.name
        if arquivo.size > limite_bytes:
            erros.append(
                f"“{nome}” tem {_mb(arquivo.size)} MB. O limite é {limite_bytes // (1024 * 1024)} MB por foto."
            )
            continue
        try:
            arquivo.seek(0)
            with Image.open(arquivo) as imagem:
                formato = imagem.format
                imagem.verify()
        except Exception:
            erros.append(f"“{nome}” não é uma imagem válida. Envie arquivos JPG, PNG ou WEBP.")
            continue
        finally:
            arquivo.seek(0)
        if formato not in FORMATOS_ACEITOS:
            erros.append(f"“{nome}” está em formato {formato}. Envie arquivos JPG, PNG ou WEBP.")
    if erros:
        raise ValidationError(erros)


def _tem_transparencia(imagem):
    if imagem.mode in ("RGBA", "LA"):
        return True
    return imagem.mode == "P" and "transparency" in imagem.info


def otimizar_imagem(arquivo):
    """Corrige a rotação EXIF, limita o lado maior a UPLOAD_MAX_LADO e recodifica (JPEG, ou WEBP se tiver transparência)."""
    arquivo.seek(0)
    with Image.open(arquivo) as original:
        original.load()
        imagem = ImageOps.exif_transpose(original)
        lado = settings.UPLOAD_MAX_LADO
        imagem.thumbnail((lado, lado), Image.Resampling.LANCZOS)
        saida = BytesIO()
        if _tem_transparencia(imagem):
            imagem.convert("RGBA").save(saida, format="WEBP", quality=QUALIDADE, method=6)
            extensao = "webp"
        else:
            imagem.convert("RGB").save(saida, format="JPEG", quality=QUALIDADE, optimize=True, progressive=True)
            extensao = "jpg"
    base = slugify(Path(arquivo.name).stem)[:60] or "foto"
    return ContentFile(saida.getvalue(), name=f"{base}.{extensao}")


def processar_upload(arquivos, categoria=None):
    """Valida e salva as fotos. Tudo ou nada: se um arquivo falhar, nenhuma foto é salva."""
    validar_arquivos(arquivos)

    otimizadas = []
    for arquivo in arquivos:
        try:
            otimizadas.append(otimizar_imagem(arquivo))
        except Exception as erro:
            raise ValidationError(
                f"“{arquivo.name}” não pôde ser processada. Envie arquivos JPG, PNG ou WEBP."
            ) from erro

    fotos = []
    try:
        with transaction.atomic():
            for conteudo in otimizadas:
                foto = Foto(categoria=categoria, publicada=True)
                foto.imagem.save(conteudo.name, conteudo, save=False)
                fotos.append(foto)
                foto.save()
    except Exception:
        for foto in fotos:
            foto.imagem.delete(save=False)
        raise
    return fotos


def fotos_publicadas():
    return Foto.objects.filter(publicada=True).select_related("categoria").order_by("ordem", "-criada_em")
