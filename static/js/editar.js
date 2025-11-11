document.addEventListener("DOMContentLoaded", function () {
  const dataInput = document.querySelector('[name="data_nascimento"]');
  if (dataInput) {
    Inputmask("99/99/9999").mask(dataInput);
  }

  Inputmask("999.999.999-99").mask(document.querySelector('[name="cpf"]'));
  Inputmask("99.999.999-9").mask(document.querySelector('[name="rg"]'));
});