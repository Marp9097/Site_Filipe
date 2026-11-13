from django.contrib.admin import AdminSite


class SuperuserAdminSite(AdminSite):
    """Django admin restrito a superusuários (o dono usa o painel próprio)."""

    site_header = "Creative Comunicação: administração técnica"
    site_title = "Creative Comunicação"

    def has_permission(self, request):
        return request.user.is_active and request.user.is_superuser
