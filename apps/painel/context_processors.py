from apps.institucional.services import nao_lidas


def painel(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or not user.is_staff:
        return {}
    return {"nao_lidas": nao_lidas()}
