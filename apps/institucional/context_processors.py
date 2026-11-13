from .models import ConfiguracaoSite


def site(request):
    config = ConfiguracaoSite.atual()
    return {"config": config, "fundo_classe": config.fundo_classe}
