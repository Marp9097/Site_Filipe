# Creative Comunicação: site institucional + painel

Projeto Django 5.2 (LTS) que atende **dois endereços** com o mesmo código:

| Endereço | Dev | Produção (previsto) | O que tem |
|----------|-----|---------------------|-----------|
| Site público | http://localhost:8000/ | www.comunicacaocreative.com.br | Home one-page + formulário de contato |
| Painel do dono | http://painel.localhost:8000/ | painel.comunicacaocreative.com.br | Login, fotos, categorias, depoimentos, mensagens, configurações e `/django-admin/` |

Quem decide é o `config/middleware.py → HostRoutingMiddleware`: se o host (sem porta) é igual a `PAINEL_HOST`,
usa `config/urls_painel.py`; qualquer outro host usa `config/urls_site.py`. Nenhuma rota do painel existe no host do site.
Os navegadores já resolvem `*.localhost` para 127.0.0.1, não precisa mexer no arquivo hosts.

## Como rodar (Windows / Git Bash)

```bash
cd clientes/creative-comunicacao/site-institucional/app
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env
# gere uma SECRET_KEY e cole no .env:
.venv/Scripts/python -c "import secrets; print(secrets.token_urlsafe(50))"
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py criar_dono        # pergunta usuário e senha
.venv/Scripts/python manage.py runserver 8000
```

- Site: http://localhost:8000/
- Painel: http://painel.localhost:8000/ (entre com o usuário criado pelo `criar_dono`)
- Django admin (só superusuário): http://painel.localhost:8000/django-admin/ (`manage.py createsuperuser`)

## Usuários

- **Não existe cadastro público.** O usuário do dono é criado com `manage.py criar_dono`
  (`--usuario`, `--email` e `--senha` são opcionais; o que faltar é perguntado, a senha sem aparecer na tela).
- O dono é `is_staff` (acessa o painel) e não é superusuário (não acessa o `/django-admin/`).
- Usuário logado sem `is_staff` recebe 403 em todas as telas do painel.

## Testes e verificações

```bash
.venv/Scripts/python manage.py check
.venv/Scripts/python manage.py makemigrations --check --dry-run
.venv/Scripts/python manage.py test
```

## Dados iniciais (data migrations)

- `portfolio/0002_categorias_iniciais`: as 5 categorias (= serviços do site atual).
- `institucional/0002_dados_iniciais`: contatos reais da Creative e os 3 depoimentos do site atual,
  **desativados** até o cliente confirmar que são reais (ative em Painel → Depoimentos).

## Estrutura

```
config/            settings/{base,dev,prod}.py · middleware.py · urls_site.py · urls_painel.py · admin.py
apps/accounts/     User customizado (AbstractUser)
apps/portfolio/    Categoria, Foto · services.processar_upload() (Pillow: valida, redimensiona, corrige EXIF)
apps/institucional ConfiguracaoSite (singleton), Depoimento, MensagemContato · views do site · context processor
apps/painel/       telas do painel (sem models) · staff_required · command criar_dono
templates/         site_base.html, institucional/, painel/
static/            css/, js/, img/
```

## Uploads

JPG, PNG ou WEBP, até 10 MB cada, no máximo 20 por envio. O conteúdo é validado com Pillow (não pela extensão),
a rotação EXIF é corrigida e o lado maior fica com no máximo 1920 px. Excluir uma foto apaga o arquivo de `media/`.
Em dev, `/media/` é servido pelo Django nos dois hosts; em produção precisa de servidor/armazenamento próprio.

## Produção (fora do escopo da rodada 1)

`config.settings.prod` (usado por `wsgi.py`/`asgi.py`): DEBUG False, HTTPS, cookies seguros, HSTS,
PostgreSQL via `DATABASE_URL`, WhiteNoise para estáticos (`collectstatic`). Preencha `CSRF_TRUSTED_ORIGINS`.

## GitHub Pages (branch `togithubpages`)

O GitHub Pages só serve arquivos estáticos, então esta branch tem na **raiz** um `index.html` gerado a partir do Django:

```bash
python manage.py gerar_estatico --url-publica https://USUARIO.github.io/REPOSITORIO/
git add index.html .nojekyll fotos static && git commit -m "Atualiza site estático"
```

- O comando usa os dados atuais do banco (configurações, fotos publicadas, depoimentos ativos), copia as fotos para `fotos/` e usa a pasta `static/` da raiz. Todos os caminhos são relativos, então funciona em subpasta.
- No GitHub: *Settings → Pages → Deploy from a branch → `togithubpages` / `(root)`*.
- **Sem servidor:** o formulário de contato abre o WhatsApp da empresa com a mensagem preenchida (ou o e-mail, se não houver WhatsApp). O painel e o `/django-admin/` continuam só no servidor (VPS); depois de mudar algo no painel, rode o `gerar_estatico` de novo e faça commit para atualizar o Pages.
