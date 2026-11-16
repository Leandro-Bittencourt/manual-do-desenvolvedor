// Comportamentos simples da interface (sem dependências externas).
document.addEventListener("DOMContentLoaded", () => {
  // Pede confirmação antes de ações irreversíveis (ex.: excluir projeto).
  document.querySelectorAll("form[data-confirmar]").forEach((form) => {
    form.addEventListener("submit", (evento) => {
      if (!window.confirm(form.dataset.confirmar)) {
        evento.preventDefault();
      }
    });
  });

  // Mostra que a análise está em andamento após o envio do .zip.
  document.querySelectorAll("form[data-processando]").forEach((form) => {
    form.addEventListener("submit", () => {
      const botao = form.querySelector("button[type=submit]");
      if (botao) {
        botao.disabled = true;
        botao.classList.add("processando");
        botao.textContent = form.dataset.processando;
      }
    });
  });
});
