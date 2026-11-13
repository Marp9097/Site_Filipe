/* Creative Comunicação: comportamento geral do site (topo fixo, menu mobile, avisos). */
(function () {
  "use strict";

  var topo = document.querySelector("[data-topo]");
  var botaoMenu = document.querySelector("[data-menu-botao]");
  var heroLogo = document.querySelector("[data-hero-logo]");

  if (topo) {
    /* Fundo do topo ao rolar */
    var atualizarRolagem = function () {
      topo.classList.toggle("topo--rolado", window.scrollY > 24);
    };
    atualizarRolagem();
    window.addEventListener("scroll", atualizarRolagem, { passive: true });

    /* O logo do topo aparece quando o logo grande do hero sai da tela */
    if (heroLogo && "IntersectionObserver" in window) {
      new IntersectionObserver(function (entradas) {
        topo.classList.toggle("topo--com-logo", !entradas[0].isIntersecting);
      }, { rootMargin: "-64px 0px 0px 0px" }).observe(heroLogo);
    } else {
      topo.classList.add("topo--com-logo");
    }
  }

  /* Menu mobile */
  if (topo && botaoMenu) {
    var fecharMenu = function (devolverFoco) {
      topo.classList.remove("topo--aberto");
      botaoMenu.setAttribute("aria-expanded", "false");
      if (devolverFoco) botaoMenu.focus();
    };

    botaoMenu.addEventListener("click", function () {
      var abrir = botaoMenu.getAttribute("aria-expanded") !== "true";
      topo.classList.toggle("topo--aberto", abrir);
      botaoMenu.setAttribute("aria-expanded", String(abrir));
    });

    topo.querySelectorAll(".topo__links a").forEach(function (link) {
      link.addEventListener("click", function () { fecharMenu(false); });
    });

    document.addEventListener("keydown", function (evento) {
      if (evento.key === "Escape" && topo.classList.contains("topo--aberto")) fecharMenu(true);
    });

    window.matchMedia("(min-width: 1024px)").addEventListener("change", function (mq) {
      if (mq.matches) fecharMenu(false);
    });
  }

  /* Fechar avisos (messages do Django) */
  document.querySelectorAll("[data-fechar-mensagem]").forEach(function (botao) {
    botao.addEventListener("click", function () {
      var aviso = botao.closest(".mensagem");
      var lista = aviso && aviso.parentElement;
      if (aviso) aviso.remove();
      if (lista && !lista.children.length) lista.remove();
    });
  });
})();
