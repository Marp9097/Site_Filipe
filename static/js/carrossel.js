/* Creative Comunicação: portfólio em carrossel
   (setas, indicadores, swipe, teclado e prefers-reduced-motion). */
(function () {
  "use strict";

  document.querySelectorAll("[data-carrossel]").forEach(function (carrossel) {
    var trilho = carrossel.querySelector("[data-trilho]");
    var slides = Array.prototype.slice.call(carrossel.querySelectorAll("[data-slide]"));
    var indicadores = Array.prototype.slice.call(carrossel.querySelectorAll("[data-indicador]"));
    var status = carrossel.querySelector("[data-status]");
    var anterior = carrossel.querySelector("[data-anterior]");
    var proxima = carrossel.querySelector("[data-proxima]");
    var total = slides.length;
    var atual = 0;
    if (!trilho || total < 2) return;

    var semMovimento = window.matchMedia("(prefers-reduced-motion: reduce)");

    function aplicarMovimento() {
      trilho.style.transition = semMovimento.matches ? "none" : "";
    }
    aplicarMovimento();
    semMovimento.addEventListener("change", aplicarMovimento);

    function irPara(indice) {
      atual = (indice + total) % total;
      trilho.style.transform = "translateX(" + (-100 * atual) + "%)";
      slides.forEach(function (slide, i) {
        slide.setAttribute("aria-hidden", String(i !== atual));
        var img = slide.querySelector("img");
        if (img && (i === atual || i === (atual + 1) % total)) img.loading = "eager";
      });
      indicadores.forEach(function (botao, i) {
        botao.setAttribute("aria-current", String(i === atual));
      });
      if (status) status.textContent = "Foto " + (atual + 1) + " de " + total;
    }

    if (anterior) anterior.addEventListener("click", function () { irPara(atual - 1); });
    if (proxima) proxima.addEventListener("click", function () { irPara(atual + 1); });
    indicadores.forEach(function (botao) {
      botao.addEventListener("click", function () {
        irPara(parseInt(botao.getAttribute("data-indicador"), 10));
      });
    });

    /* Teclado: setas com o carrossel (ou um controle dele) em foco */
    carrossel.addEventListener("keydown", function (evento) {
      if (evento.key === "ArrowLeft") { evento.preventDefault(); irPara(atual - 1); }
      else if (evento.key === "ArrowRight") { evento.preventDefault(); irPara(atual + 1); }
      else if (evento.key === "Home") { evento.preventDefault(); irPara(0); }
      else if (evento.key === "End") { evento.preventDefault(); irPara(total - 1); }
    });

    /* Swipe (toque e mouse), sem bloquear a rolagem vertical */
    var inicioX = null;
    var inicioY = 0;
    var largura = 1;
    var janela = carrossel.querySelector(".carrossel__janela");

    janela.addEventListener("pointerdown", function (evento) {
      if (evento.pointerType === "mouse" && evento.button !== 0) return;
      inicioX = evento.clientX;
      inicioY = evento.clientY;
      largura = janela.clientWidth || 1;
      trilho.style.transition = "none";
    });

    janela.addEventListener("pointermove", function (evento) {
      if (inicioX === null) return;
      var dx = evento.clientX - inicioX;
      if (Math.abs(evento.clientY - inicioY) > Math.abs(dx)) return;
      trilho.style.transform = "translateX(calc(" + (-100 * atual) + "% + " + dx + "px))";
    });

    function terminar(evento) {
      if (inicioX === null) return;
      var dx = evento.clientX - inicioX;
      inicioX = null;
      aplicarMovimento();
      if (Math.abs(dx) > Math.min(80, largura * 0.18)) irPara(atual + (dx < 0 ? 1 : -1));
      else irPara(atual);
    }
    janela.addEventListener("pointerup", terminar);
    janela.addEventListener("pointercancel", terminar);
    janela.addEventListener("pointerleave", function (evento) { if (inicioX !== null) terminar(evento); });

    irPara(0);
  });
})();
