from django.conf import settings
from django.http.request import split_domain_port

URLCONF_PAINEL = "config.urls_painel"


class HostRoutingMiddleware:
    """Escolhe o URLconf pelo host: PAINEL_HOST usa o painel; qualquer outro usa o site."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        dominio, _porta = split_domain_port(request.get_host())
        if dominio == settings.PAINEL_HOST.lower():
            request.urlconf = URLCONF_PAINEL
        return self.get_response(request)
