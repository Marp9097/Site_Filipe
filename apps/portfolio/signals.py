from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Foto


@receiver(post_delete, sender=Foto)
def apagar_arquivo_da_foto(sender, instance, **kwargs):
    if instance.imagem:
        instance.imagem.delete(save=False)
