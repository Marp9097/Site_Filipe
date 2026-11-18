/* Versão estática (GitHub Pages): sem servidor para receber o formulário,
   a mensagem é montada e aberta no WhatsApp da empresa (ou no e-mail, se não houver WhatsApp). */
(function () {
  "use strict";

  var form = document.querySelector("[data-contato-estatico]");
  if (!form) return;

  function valor(nome) {
    var campo = form.elements[nome];
    if (!campo) return "";
    if (campo.tagName === "SELECT") {
      var opcao = campo.options[campo.selectedIndex];
      return opcao && campo.value ? opcao.text : "";
    }
    return (campo.value || "").trim();
  }

  form.addEventListener("submit", function (evento) {
    evento.preventDefault();
    if (!form.reportValidity()) return;

    var linhas = [
      "Olá! Vim pelo site e gostaria de solicitar um orçamento.",
      "",
      "Nome: " + valor("nome"),
      "E-mail: " + valor("email"),
      "Telefone: " + valor("telefone"),
    ];
    var servico = valor("servico");
    if (servico) linhas.push("Serviço: " + servico);
    linhas.push("", valor("mensagem"));
    var texto = linhas.join("\n");

    var numero = (form.dataset.numero || "").replace(/\D/g, "");
    if (form.dataset.whatsapp && numero) {
      window.open("https://wa.me/" + numero + "?text=" + encodeURIComponent(texto), "_blank", "noopener");
    } else if (form.dataset.email) {
      window.location.href = "mailto:" + form.dataset.email +
        "?subject=" + encodeURIComponent("Orçamento pelo site") +
        "&body=" + encodeURIComponent(texto);
    }
  });
})();
