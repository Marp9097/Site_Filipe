/* Versão estática (GitHub Pages): sem servidor para receber o formulário,
   a mensagem é montada já formatada e aberta no WhatsApp da empresa
   (ou no e-mail, se não houver WhatsApp cadastrado). */
(function () {
  "use strict";

  var form = document.querySelector("[data-contato-estatico]");
  if (!form) return;

  var telefone = form.elements.telefone;

  function valor(nome) {
    var campo = form.elements[nome];
    if (!campo) return "";
    if (campo.tagName === "SELECT") {
      var opcao = campo.options[campo.selectedIndex];
      return opcao && campo.value ? opcao.text.trim() : "";
    }
    return (campo.value || "").trim();
  }

  function digitos(texto) {
    return (texto || "").replace(/\D/g, "");
  }

  /* (31) 99999-9999 / (31) 3333-4444; outros formatos ficam como foram digitados */
  function formatarTelefone(texto) {
    var d = digitos(texto);
    if (d.length === 13 && d.indexOf("55") === 0) d = d.slice(2);
    if (d.length === 12 && d.indexOf("55") === 0) d = d.slice(2);
    if (d.length === 11) return "(" + d.slice(0, 2) + ") " + d.slice(2, 7) + "-" + d.slice(7);
    if (d.length === 10) return "(" + d.slice(0, 2) + ") " + d.slice(2, 6) + "-" + d.slice(6);
    return texto;
  }

  /* Mesma regra do servidor: telefone com DDD (10 a 13 dígitos) */
  function validarTelefone() {
    if (!telefone) return;
    var n = digitos(telefone.value).length;
    telefone.setCustomValidity(
      telefone.value && (n < 10 || n > 13) ? "Informe o telefone com DDD, ex.: (31) 99999-9999." : ""
    );
  }
  if (telefone) telefone.addEventListener("input", validarTelefone);

  /* Emojis ficam de fora de propósito: no WhatsApp Web eles às vezes chegam como "?" via link. */
  function montarMensagem() {
    var linhas = [
      "*NOVO PEDIDO DE ORÇAMENTO*",
      "_Enviado pelo site da Creative Comunicação_",
      "",
      "*Nome:* " + valor("nome"),
      "*Telefone/WhatsApp:* " + formatarTelefone(valor("telefone")),
      "*E-mail:* " + valor("email"),
    ];
    var servico = valor("servico");
    if (servico) linhas.push("*Serviço:* " + servico);
    linhas.push("", "*Mensagem:*", valor("mensagem"));
    return linhas.join("\n");
  }

  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    validarTelefone();
    if (!form.reportValidity()) return;

    var texto = montarMensagem();
    var numero = digitos(form.dataset.numero);
    if (form.dataset.whatsapp && numero) {
      window.open("https://wa.me/" + numero + "?text=" + encodeURIComponent(texto), "_blank", "noopener");
    } else if (form.dataset.email) {
      window.location.href = "mailto:" + form.dataset.email +
        "?subject=" + encodeURIComponent("Pedido de orçamento pelo site") +
        "&body=" + encodeURIComponent(texto.replace(/[*_]/g, ""));
    }
  });
})();
