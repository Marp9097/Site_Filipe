from django.contrib import admin

from .models import Categoria, Foto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nome", "slug", "ordem"]
    list_editable = ["ordem"]
    prepopulated_fields = {"slug": ["nome"]}


@admin.register(Foto)
class FotoAdmin(admin.ModelAdmin):
    list_display = ["__str__", "categoria", "publicada", "ordem", "criada_em"]
    list_filter = ["publicada", "categoria"]
    list_editable = ["publicada", "ordem"]
    list_select_related = ["categoria"]
