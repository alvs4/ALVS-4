document.addEventListener('DOMContentLoaded', () => {
  const alunos = document.querySelectorAll('[id^="notaForm"]');

  alunos.forEach(form => {
    const alunoId = form.id.replace('notaForm', '');
    const modalEl = document.getElementById(`modalNota${alunoId}`);

    if (form && modalEl) {
      modalEl.addEventListener('shown.bs.modal', () => {
        checkNotas(alunoId);
      });

      form.addEventListener('submit', function (e) {
        e.preventDefault();

        let valid = true;
        form.querySelectorAll('input[type="number"]').forEach(input => {
          const value = input.value;
          if (input.hasAttribute("required") && (value === '' || isNaN(value) || value < 0 || value > 100)) {
            input.classList.add("is-invalid");
            valid = false;
          } else {
            input.classList.remove("is-invalid");
          }
        });

        if (!valid) return;

        const formData = new FormData(this);

        fetch(window.URL_INSERIR_NOTA, {
          method: "POST",
          headers: {
            "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
          },
          body: formData
        })
        .then(response => response.json())
        .then(data => {
          const badgeArea = document.getElementById(`statusBadge${alunoId}`);
          badgeArea.innerHTML = `<span class="badge ${data.badge_class} px-3 py-2">${data.status}</span>`;

          const modal = bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();
        })
        .catch(error => {
          console.error("Erro ao enviar notas:", error);
        });
      });

      form.querySelectorAll('input').forEach(input => {
        input.addEventListener("input", () => checkNotas(alunoId));
      });
    }
  });
});

function aplicarNota(alunoId) {
  checkNotas(alunoId);
}

function salvarNota(alunoId) {
  const form = document.getElementById(`notaForm${alunoId}`);
  if (!form) return;
  form.dispatchEvent(new Event('submit'));
}

function checkNotas(alunoId) {
  const modal = document.getElementById(`modalNota${alunoId}`);
  if (!modal) return;

  const getInputVal = (name) => {
    const el = modal.querySelector(`[name="${name}"]`);
    return el && el.value !== "" ? parseFloat(el.value) : null;
  };

  const n1s1 = getInputVal("nota_1_semestre1");
  const n2s1 = getInputVal("nota_2_semestre1");
  const paralela1 = getInputVal("paralela_1");

  const n1s2 = getInputVal("nota_1_semestre2");
  const n2s2 = getInputVal("nota_2_semestre2");
  const paralela2 = getInputVal("paralela_2");

  const recuperacao = getInputVal("nota_recuperacao");

  const paralela1Row = document.getElementById(`paralela1-row-${alunoId}`);
  const paralela2Row = document.getElementById(`paralela2-row-${alunoId}`);
  const finalSection = document.getElementById(`final-section-${alunoId}`);
  const statusBadge = document.getElementById(`statusBadge${alunoId}`);

  finalSection?.classList.add("d-none");
  statusBadge.innerHTML = "";

  if (n1s1 !== null && n2s1 !== null && (n1s1 + n2s1 < 60)) {
    paralela1Row?.classList.remove("d-none");
  } else {
    paralela1Row?.classList.add("d-none");
  }

  if (n1s2 !== null && n2s2 !== null && (n1s2 + n2s2 < 60)) {
    paralela2Row?.classList.remove("d-none");
  } else {
    paralela2Row?.classList.add("d-none");
  }

  if ([n1s1, n2s1, n1s2, n2s2].every(v => v !== null)) {
    const somaS1 = n1s1 + n2s1;
    const somaS2 = n1s2 + n2s2;

    const media1 = paralela1 !== null ? Math.max(somaS1, paralela1) : somaS1;
    const media2 = paralela2 !== null ? Math.max(somaS2, paralela2) : somaS2;
    const total = media1 + media2;

    let status = "", badge = "";

    if (total >= 120) {
      status = "Aprovado";
      badge = "bg-success text-white";
    } else {
      finalSection?.classList.remove("d-none");

      if (recuperacao !== null) {
        const finalTotal = Math.max(media1, 60) + Math.max(media2, 60) + recuperacao;

        if (finalTotal >= 180) {
          status = "Aprovado";
          badge = "bg-success text-white";
        } else {
          status = "Reprovado na Final";
          badge = "bg-danger text-white";
        }
      } else {
        status = "Requer Final";
        badge = "bg-warning text-dark";
      }
    }

    statusBadge.innerHTML = `<span class="badge ${badge} px-3 py-2">${status}</span>`;
  }
}

window.salvarNota = salvarNota;
window.aplicarNota = aplicarNota;