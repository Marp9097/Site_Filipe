"""Monta o portfólio do index.html a partir da pasta fotos/ e do arquivo modo-fotos.txt.

Só usa a biblioteca padrão do Python (roda no GitHub Actions sem instalar nada):

    python scripts/montar_portfolio.py

- fotos/               fotos sem categoria
- fotos/<Categoria>/   cada subpasta vira uma categoria (o nome da pasta é o nome exibido)
- modo-fotos.txt       "galeria" ou "carrossel"

O trecho entre <!-- PORTFOLIO:INICIO --> e <!-- PORTFOLIO:FIM --> (e o dos scripts) é reescrito.
"""

import re
import sys
import unicodedata
from html import escape
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FOTOS = "fotos"
ARQUIVO_MODO = "modo-fotos.txt"
EXTENSOES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
MODOS = {"galeria", "carrossel"}
AVISO_TAMANHO = 3 * 1024 * 1024
ALT_PADRAO = "Trabalho da Creative Comunicação"


def slug(texto):
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def ler_modo(raiz):
    arquivo = raiz / ARQUIVO_MODO
    if not arquivo.exists():
        return "galeria"
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        palavra = linha.split("#", 1)[0].strip().lower()
        if palavra:
            if palavra in MODOS:
                return palavra
            print(f"Aviso: '{palavra}' em {ARQUIVO_MODO} não é 'galeria' nem 'carrossel'. Usando galeria.")
            return "galeria"
    return "galeria"


def listar_fotos(raiz):
    """Lista [{src, alt, categoria, slug}] em ordem: sem categoria primeiro, depois por pasta e nome."""
    pasta = raiz / PASTA_FOTOS
    if not pasta.is_dir():
        return []
    fotos = []
    arquivos = sorted(
        (a for a in pasta.rglob("*") if a.is_file() and a.suffix.lower() in EXTENSOES),
        key=lambda a: (len(a.relative_to(pasta).parts) > 1, str(a.relative_to(pasta)).lower()),
    )
    for arquivo in arquivos:
        relativo = arquivo.relative_to(pasta)
        categoria = relativo.parts[0] if len(relativo.parts) > 1 else ""
        if arquivo.stat().st_size > AVISO_TAMANHO:
            print(f"Aviso: {relativo} tem mais de 3 MB; reduza para o site carregar mais rápido.")
        fotos.append({
            "src": PASTA_FOTOS + "/" + quote(relativo.as_posix()),
            "alt": f"{ALT_PADRAO}: {categoria}" if categoria else ALT_PADRAO,
            "categoria": categoria,
            "slug": slug(categoria),
        })
    return fotos


def html_carrossel(fotos):
    total = len(fotos)
    slides = []
    for i, f in enumerate(fotos, start=1):
        legenda = ""
        if f["categoria"]:
            legenda = f'\n                  <p class="carrossel__legenda">Trabalho da Creative<small>{escape(f["categoria"])}</small></p>'
        slides.append(
            f'                <li class="carrossel__slide" role="group" aria-roledescription="slide" aria-label="{i} de {total}" data-slide>\n'
            f'                  <img src="{escape(f["src"])}" alt="{escape(f["alt"])}" loading="lazy" draggable="false">{legenda}\n'
            f"                </li>"
        )
    partes = [
        '        <div id="portfolio-fotos" class="portfolio portfolio--carrossel" data-modo="carrossel">',
        '          <div class="carrossel" data-carrossel role="region" aria-roledescription="carrossel" aria-label="Fotos dos nossos trabalhos" tabindex="0">',
        '            <div class="carrossel__janela">',
        '              <ul class="carrossel__trilho" role="list" data-trilho>',
        *slides,
        "              </ul>",
    ]
    if total > 1:
        partes += [
            '              <button class="carrossel__seta carrossel__seta--anterior" type="button" aria-label="Foto anterior" data-anterior><svg aria-hidden="true"><use href="#i-seta-esq"></use></svg></button>',
            '              <button class="carrossel__seta carrossel__seta--proxima" type="button" aria-label="Próxima foto" data-proxima><svg aria-hidden="true"><use href="#i-seta-dir"></use></svg></button>',
        ]
    partes.append("            </div>")
    if total > 1:
        partes.append('            <ol class="carrossel__indicadores" role="list">')
        for i in range(total):
            atual = "true" if i == 0 else "false"
            partes.append(
                f'              <li><button class="carrossel__indicador" type="button" aria-label="Ir para a foto {i + 1}" aria-current="{atual}" data-indicador="{i}"></button></li>'
            )
        partes += [
            "            </ol>",
            f'            <p class="carrossel__status" aria-live="polite" data-status>Foto 1 de {total}</p>',
        ]
    partes += ["          </div>", "        </div>"]
    return "\n".join(partes)


def html_galeria(fotos):
    categorias = []
    for f in fotos:
        if f["categoria"] and (f["categoria"], f["slug"]) not in categorias:
            categorias.append((f["categoria"], f["slug"]))
    partes = ['        <div id="portfolio-fotos" class="portfolio portfolio--galeria" data-modo="galeria">']
    if len(categorias) > 1:
        partes.append('          <div class="filtros" role="group" aria-label="Filtrar fotos por categoria">')
        partes.append('            <button class="chip" type="button" data-filtro="todas" aria-pressed="true">Todas</button>')
        for nome, s in categorias:
            partes.append(f'            <button class="chip" type="button" data-filtro="{s}" aria-pressed="false">{escape(nome)}</button>')
        partes.append("          </div>")
    partes.append('          <ul class="galeria" role="list" data-galeria>')
    for f in fotos:
        src, alt, cat = escape(f["src"]), escape(f["alt"]), escape(f["categoria"])
        partes += [
            f'            <li class="galeria__item" data-categoria="{f["slug"]}">',
            f'              <a class="galeria__link" href="{src}" data-ampliar data-legenda="{cat}" aria-label="Ampliar foto: {alt}">',
            f'                <img src="{src}" alt="{alt}" loading="lazy">',
            "              </a>",
            "            </li>",
        ]
    partes += [
        "          </ul>",
        '          <p class="portfolio__filtro-vazio" hidden data-filtro-vazio>Nenhuma foto nessa categoria por enquanto.</p>',
        "",
        '          <dialog class="lightbox" aria-label="Foto ampliada" data-lightbox>',
        '            <button class="lightbox__botao lightbox__fechar" type="button" aria-label="Fechar" data-fechar><svg aria-hidden="true"><use href="#i-fechar"></use></svg></button>',
        '            <button class="lightbox__botao lightbox__anterior" type="button" aria-label="Foto anterior" data-anterior><svg aria-hidden="true"><use href="#i-seta-esq"></use></svg></button>',
        '            <figure class="lightbox__figura">',
        '              <img alt="" data-imagem>',
        '              <figcaption class="lightbox__legenda"><span data-legenda></span> <span class="lightbox__contador" data-contador></span></figcaption>',
        "            </figure>",
        '            <button class="lightbox__botao lightbox__proxima" type="button" aria-label="Próxima foto" data-proxima><svg aria-hidden="true"><use href="#i-seta-dir"></use></svg></button>',
        "          </dialog>",
        "        </div>",
    ]
    return "\n".join(partes)


def html_vazio(instagram):
    botao = ""
    texto_insta = ""
    if instagram:
        texto_insta = " Enquanto isso, veja mais no nosso Instagram."
        botao = (
            f'\n          <a class="botao botao--secundario" href="{escape(instagram)}" target="_blank" rel="noopener">'
            '<svg aria-hidden="true"><use href="#i-instagram"></use></svg>Ver no Instagram'
            '<span class="visualmente-oculto"> (abre em nova aba)</span></a>'
        )
    return (
        '        <div class="portfolio__vazio">\n'
        '          <svg aria-hidden="true"><use href="#i-imagem"></use></svg>\n'
        "          <strong>Novas fotos chegando em breve</strong>\n"
        f"          <p>Estamos selecionando os melhores trabalhos para mostrar aqui.{texto_insta}</p>{botao}\n"
        "        </div>"
    )


def substituir(html, marcador, conteudo):
    inicio, fim = f"<!-- {marcador}:INICIO -->", f"<!-- {marcador}:FIM -->"
    padrao = re.compile(re.escape(inicio) + r".*?" + re.escape(fim), re.S)
    if not padrao.search(html):
        sys.exit(f"Erro: marcadores {inicio} / {fim} não encontrados no index.html.")
    return padrao.sub(lambda _m: f"{inicio}\n{conteudo}\n{fim}", html, count=1)


def montar(raiz=RAIZ):
    index = raiz / "index.html"
    html = index.read_text(encoding="utf-8")
    modo = ler_modo(raiz)
    fotos = listar_fotos(raiz)

    if not fotos:
        achado = re.search(r'href="(https://(?:www\.)?instagram\.com/[^"]+)"', html)
        portfolio = html_vazio(achado.group(1) if achado else "")
        scripts = ""
    elif modo == "carrossel":
        portfolio = html_carrossel(fotos)
        scripts = '<script src="static/js/carrossel.js" defer></script>'
    else:
        portfolio = html_galeria(fotos)
        scripts = '<script src="static/js/galeria.js" defer></script>'

    html = substituir(html, "PORTFOLIO", portfolio)
    html = substituir(html, "PORTFOLIO-JS", scripts)
    index.write_text(html, encoding="utf-8")
    print(f"Portfólio montado: {len(fotos)} foto(s), modo {modo}.")


if __name__ == "__main__":
    montar()
