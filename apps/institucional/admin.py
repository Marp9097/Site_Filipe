from django.contrib import admin

from .models import ConfiguracaoSite, Depoimento, MensagemContato


@admin.register(ConfiguracaoSite)
class ConfiguracaoSiteAdmin(admin.ModelAdmin):
    list_display = ["__str__", "fundo", "modo_fotos", "telefone", "email", "atualizado_em"]

    def has_add_permission(self, request):
        return not ConfiguracaoSite.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Depoimento)
class DepoimentoAdmin(admin.ModelAdmin):
    list_display = ["nome", "empresa", "nota", "ativo", "ordem"]
    list_filter = ["ativo"]
    list_editable = ["ativo", "ordem"]


@admin.register(MensagemContato)
class MensagemContatoAdmin(admin.ModelAdmin):
    list_display = ["nome", "email", "telefone", "servico", "lida", "criada_em"]
    list_filter = ["lida", "servico"]
    search_fields = ["nome", "email", "telefone", "mensagem"]
    date_hierarchy = "criada_em"
