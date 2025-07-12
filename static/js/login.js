// Espera o carregamento da página
window.addEventListener("DOMContentLoaded", function () {
  const mensagem = document.getElementById("mensagem-erro");

  if (mensagem) {
    // Espera 4 segundos e esconde
    setTimeout(() => {
      mensagem.style.display = "none";
    }, 4000);
  }
});
