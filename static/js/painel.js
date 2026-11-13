/* Creative Comunicação: painel (gaveta do menu, confirmação de exclusão, prévia do upload). */
(function () {
  "use strict";

  /* ---------- Gaveta do menu (mobile) ---------- */
  var menu = document.querySelector("[data-menu]");
  var botaoAbrir = document.querySelector("[data-abrir-menu]");
  var sombra = document.querySelector(".p-sombra");
  var desktop = window.matchMedia("(min-width: 1024px)");

  function abrirMenu() {
    menu.classList.add("p-lateral--aberta");
    botaoAbrir.setAttribute("aria-expanded", "true");
    if (sombra) sombra.hidden = false;
    document.body.style.overflow = "hidden";
    var primeiro = menu.querySelector("a, button");
    if (primeiro) primeiro.focus();
  }

  function fecharMenu(devolverFoco) {
    menu.classList.remove("p-lateral--aberta");
    botaoAbrir.setAttribute("aria-expanded", "false");
    if (sombra) sombra.hidden = true;
    document.body.style.overflow = "";
    if (devolverFoco) botaoAbrir.focus();
  }

  if (menu && botaoAbrir) {
    botaoAbrir.addEventListener("click", abrirMenu);
    document.querySelectorAll("[data-fechar-menu]").forEach(function (el) {
      el.addEventListener("click", function () { fecharMenu(true); });
    });
    document.addEventListener("keydown", function (evento) {
      if (!menu.classList.contains("p-lateral--aberta") || desktop.matches) return;
      if (evento.key === "Escape") { fecharMenu(true); return; }
      if (evento.key === "Tab") {
        var focaveis = menu.querySelectorAll("a, button");
        var primeiro = focaveis[0];
        var ultimo = focaveis[focaveis.length - 1];
        if (evento.shiftKey && document.activeElement === primeiro) { evento.preventDefault(); ultimo.focus(); }
        else if (!evento.shiftKey && document.activeElement === ultimo) { evento.preventDefault(); primeiro.focus(); }
      }
    });
    desktop.addEventListener("change", function (mq) { if (mq.matches) fecharMenu(false); });
  }

  /* ---------- Confirmação antes de excluir ---------- */
  document.querySelectorAll("form[data-confirmar]").forEach(function (form) {
    form.addEventListener("submit", function (evento) {
      if (!window.confirm(form.getAttribute("data-confirmar"))) evento.preventDefault();
    });
  });

  /* ---------- Prévia das imagens selecionadas no upload ---------- */
  var LIMITE_BYTES = 10 * 1024 * 1024;
  var LIMITE_ARQUIVOS = 20;
  var TIPOS = ["image/jpeg", "image/png", "image/webp"];

  var previa = document.querySelector("[data-previa]");
  var entrada = document.querySelector('.p-upload input[type="file"]');
  if (!previa || !entrada) return;

  var lista = previa.querySelector("[data-previa-lista]");
  var resumo = previa.querySelector("[data-previa-resumo]");
  var area = entrada.closest(".p-upload__area");
  var urls = [];

  function tamanho(bytes) {
    var mb = bytes / (1024 * 1024);
    return mb >= 1 ? mb.toFixed(1).replace(".", ",") + " MB" : Math.max(1, Math.round(bytes / 1024)) + " KB";
  }

  function atualizar() {
    urls.forEach(URL.revokeObjectURL);
    urls = [];
    lista.innerHTML = "";
    var arquivos = Array.prototype.slice.call(entrada.files || []);
    previa.hidden = arquivos.length === 0;
    if (!arquivos.length) return;

    var problemas = 0;
    arquivos.forEach(function (arquivo) {
      var item = document.createElement("li");
      item.className = "p-previa__item";
      var img = document.createElement("img");
      img.alt = "";
      var legenda = document.createElement("span");
      var erro = "";
      if (TIPOS.indexOf(arquivo.type) === -1) erro = "Não é JPG, PNG ou WEBP";
      else if (arquivo.size > LIMITE_BYTES) erro = "Maior que 10 MB";
      if (erro) {
        problemas += 1;
        item.classList.add("p-previa__item--erro");
        legenda.textContent = arquivo.name + ": " + erro;
      } else {
        var url = URL.createObjectURL(arquivo);
        urls.push(url);
        img.src = url;
        legenda.textContent = arquivo.name + " · " + tamanho(arquivo.size);
      }
      legenda.title = arquivo.name;
      item.appendChild(img);
      item.appendChild(legenda);
      lista.appendChild(item);
    });

    var texto = arquivos.length + (arquivos.length === 1 ? " foto selecionada." : " fotos selecionadas.");
    if (arquivos.length > LIMITE_ARQUIVOS) texto += " O limite é " + LIMITE_ARQUIVOS + " por envio: tire algumas antes de enviar.";
    else if (problemas) texto += " " + problemas + (problemas === 1 ? " arquivo não será aceito" : " arquivos não serão aceitos") + " (marcados em vermelho).";
    resumo.textContent = texto;
    resumo.classList.toggle("erros", arquivos.length > LIMITE_ARQUIVOS || problemas > 0);
  }

  entrada.addEventListener("change", atualizar);
  if (area) {
    ["dragenter", "dragover"].forEach(function (tipo) {
      entrada.addEventListener(tipo, function () { area.classList.add("p-upload__area--arrastando"); });
    });
    ["dragleave", "drop"].forEach(function (tipo) {
      entrada.addEventListener(tipo, function () { area.classList.remove("p-upload__area--arrastando"); });
    });
  }
})();
