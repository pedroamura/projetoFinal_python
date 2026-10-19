document.addEventListener("DOMContentLoaded", () => {
    const selectLab = document.getElementById("filtro-lab");
    const tabelaCorpo = document.querySelector("#tabela-grade tbody");
    const modal = document.getElementById("modal-reserva");
    const fecharModalBtn = document.getElementById("fechar-modal");
    const formReserva = document.getElementById("form-reserva");
    const infoSlot = document.getElementById("info-slot");

    let dadosGlobais = {};
    let reservasGlobais = {};
    let slotSelecionado = null;

    async function carregarGrade() {
        const resposta = await fetch("/api/grade");
        const resultado = await resposta.json();
        dadosGlobais = resultado.grade;
        reservasGlobais = resultado.reservas;
        renderizarTabela();
    }

    function renderizarTabela() {
        tabelaCorpo.innerHTML = "";
        const labSelecionado = selectLab.value;
        const dias = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta"];
        
        // Pega os horários baseados no LAB A de segunda-feira como referência estrutural
        const horarios = Object.keys(dadosGlobais["Segunda"][labSelecionado] || {});

        horarios.forEach(horario => {
            const tr = document.createElement("tr");
            
            // Coluna de Horário
            const tdHorario = document.createElement("td");
            tdHorario.textContent = horario;
            tr.appendChild(tdHorario);

            // Colunas dos dias da semana
            dias.forEach(dia => {
                const td = document.createElement("td");
                const chaveSlot = `${dia}_${labSelecionado}_${horario}`;
                
                const aulaFixa = dadosGlobais[dia]?.[labSelecionado]?.[horario] || "LIVRE";
                const reservaDinamica = reservasGlobais[chaveSlot];

                if (reservaDinamica) {
                    td.textContent = `Reservado: ${reservaDinamica.professor} (${reservaDinamica.data})`;
                    td.className = "ocupado";
                } else if (aulaFixa !== "LIVRE") {
                    td.textContent = aulaFixa;
                    td.className = "ocupado";
                } else {
                    td.textContent = "LIVRE";
                    td.className = "livre";
                    td.onclick = () => abrirModal(dia, labSelecionado, horario);
                }

                tr.appendChild(td);
            });

            tabelaCorpo.appendChild(tr);
        });
    }

    function abrirModal(dia, laboratorio, horario) {
        slotSelecionado = { dia, laboratorio, horario };
        infoSlot.textContent = `${laboratorio} - ${dia} às ${horario}`;
        
        // Define data mínima para exatamente 7 dias à frente
        const hoje = new Date();
        hoje.setDate(hoje.getDate() + 7);
        document.getElementById("data-reserva").min = hoje.toISOString().split("T")[0];
        
        modal.style.display = "block";
    }

    fecharModalBtn.onclick = () => { modal.style.display = "none"; };

    formReserva.onsubmit = async (e) => {
        e.preventDefault();
        const professor = document.getElementById("nome-professor").value;
        const data = document.getElementById("data-reserva").value;

        const payload = {
            dia: slotSelecionado.dia,
            laboratorio: slotSelecionado.laboratorio,
            horario: slotSelecionado.horario,
            professor: professor,
            data: data
        };

        const resposta = await fetch("/api/reservar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const resultado = await resposta.json();
        alert(resultado.mensagem);

        if (resultado.sucesso) {
            modal.style.display = "none";
            formReserva.reset();
            carregarGrade();
        }
    };

    selectLab.onchange = renderizarTabela;

    carregarGrade();
});