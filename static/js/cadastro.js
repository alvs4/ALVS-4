document.addEventListener("DOMContentLoaded", function () {
    const dataInput = document.querySelector('[name="data_nascimento"]');
    if (dataInput) {
        Inputmask("99/99/9999").mask(dataInput);
    }
    
    const cpfInput = document.querySelector('[name="cpf"]');
    if (cpfInput) {
        Inputmask("999.999.999-99").mask(cpfInput);
    }

    const rgInput = document.querySelector('[name="rg"]');
    if (rgInput) {
        Inputmask("99.999.999-9").mask(rgInput);
    }

    const cepInput = document.querySelector('[name="endereco_cep"]');
    if (cepInput) {
        Inputmask("99999-999").mask(cepInput);
    }

    const telefoneInput = document.querySelector('[name="telefone"]');
    if (telefoneInput) {
        Inputmask({
             mask: ["(99) 9999-9999", "(99) 99999-9999"], 
             keepStatic: true,
             greedy: false
        }).mask(telefoneInput);
    }
});