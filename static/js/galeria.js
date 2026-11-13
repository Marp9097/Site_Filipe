/* Creative Comunicação: portfólio em galeria (filtro por categoria + lightbox acessível).
   Sem JS, cada foto é um link para a imagem em tamanho real. */
(function () {
  "use strict";

  var galeria = document.querySelector("[data-galeria]");
  if (!galeria) return;

  var itens = Array.prototype.slice.call(galeria.querySelectorAll(".galeria__item"));
  var avisoVazio = document.querySelector("[data-filtro-vazio]");

  /* ---------- Filtro por categoria ---------- */
  var botoesFiltro = document.querySelectorAll("[data-filtro]");
  botoesFiltro.forEach(function (botao) {
    botao.addEventListener("click", function () {
      var filtro = botao.getAttribute("data-filtro");
      botoesFiltro.forEach(function (b) { b.setAttribute("aria-pressed", String(b === botao)); });
      var visiveis = 0;
      itens.forEach(function (item) {
        var mostrar = filtro === "todas" || item.getAttribute("data-categoria") === filtro;
        item.hidden = !mostrar;
        if (mostrar) visiveis += 1;
      });
      if (avisoVazio) avisoVazio.hidden = visiveis > 0;
    });
  });

  /* ---------- Lightbox (dialog nativo) ---------- */
  var dialogo = document.querySelector("[data-lightbox]");
  if (!dialogo || typeof dialogo.showModal !== "function") return;

  var imagem = dialogo.querySelector("[data-imagem]");
  var legenda = dialogo.querySelector("[data-legenda]");
  var contador = dialogo.querySelector("[data-contador]");
  var botaoFechar = dialogo.querySelector("[data-fechar]");
  var botaoAnterior = dialogo.querySelector("[data-anterior]");
  var botaoProxima = dialogo.querySelector("[data-proxima]");
  var lista = [];
  var atual = 0;
  var origem = null;

  function linksVisiveis() {
    return itens.filter(function (item) { return !item.hidden; })
      .map(function (item) { return item.querySelector("[data-ampliar]"); });
  }

  function mostrar(indice) {
    atual = (indice + lista.length) % lista.length;
    var link = lista[atual];
    var miniatura = link.querySelector("img");
    imagem.src = link.getAttribute("href");
    imagem.alt = miniatura ? miniatura.alt : "";
    legenda.textContent = link.getAttribute("data-legenda") || "";
    contador.textContent = lista.length > 1 ? "(" + (atual + 1) + " de " + lista.length + ")" : "";
    var varias = lista.length > 1;
    botaoAnterior.hidden = !varias;
    botaoProxima.hidden = !varias;
  }

  function abrir(link) {
    lista = linksVisiveis();
    origem = link;
    mostrar(Math.max(0, lista.indexOf(link)));
    dialogo.showModal();
    botaoFechar.focus();
  }

  function fechar() {
    if (dialogo.open) dialogo.close();
  }

  galeria.addEventListener("click", function (evento) {
    var link = evento.target.closest("[data-ampliar]");
    if (!link) return;
    evento.preventDefault();
    abrir(link);
  });

  botaoFechar.addEventListener("click", fechar);
  botaoAnterior.addEventListener("click", function () { mostrar(atual - 1); });
  botaoProxima.addEventListener("click", function () { mostrar(atual + 1); });

  /* Clique fora da foto (no fundo escuro) fecha */
  dialogo.addEventListener("click", function (evento) {
    if (evento.target === dialogo) fechar();
  });

  dialogo.addEventListener("keydown", function (evento) {
    if (evento.key === "ArrowLeft" && lista.length > 1) { evento.preventDefault(); mostrar(atual - 1); }
    else if (evento.key === "ArrowRight" && lista.length > 1) { evento.preventDefault(); mostrar(atual + 1); }
    else if (evento.key === "Tab") {
      /* Foco preso dentro do lightbox */
      var focaveis = Array.prototype.filter.call(
        dialogo.querySelectorAll("button"), function (b) { return !b.hidden; }
      );
      var primeiro = focaveis[0];
      var ultimo = focaveis[focaveis.length - 1];
      if (evento.shiftKey && document.activeElement === primeiro) { evento.preventDefault(); ultimo.focus(); }
      else if (!evento.shiftKey && document.activeElement === ultimo) { evento.preventDefault(); primeiro.focus(); }
    }
  });

  /* Esc é tratado pelo próprio <dialog>; ao fechar, o foco volta para a foto de origem */
  dialogo.addEventListener("close", function () {
    imagem.removeAttribute("src");
    if (origem) origem.focus();
  });
})();
