document.addEventListener("DOMContentLoaded", () => {
    const selectLab = document.getElementById("filtro-lab");
    const tabelaCorpo = document.querySelector("#tabela-grade tbody");

    // Modais e formulários
    const modalReserva = document.getElementById("modal-reserva");
    const fecharModalBtn = document.getElementById("fechar-modal");
    const formReserva = document.getElementById("form-reserva");
    const infoSlot = document.getElementById("info-slot");

    const modalCancelar = document.getElementById("modal-cancelar");
    const fecharModalCancelarBtn = document.getElementById("fechar-modal-cancelar");
    const formCancelar = document.getElementById("form-cancelar");
    const infoSlotCancelar = document.getElementById("info-slot-cancelar");

    let dadosGlobais = {};
    let reservasGlobais = {};
    let slotSelecionado = null;
    let slotParaCancelar = null;

    const dias = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta"];

    function obterDataDoDiaDaSemana(diaNome) {
        const mapaDias = { "Segunda": 1, "Terca": 2, "Quarta": 3, "Quinta": 4, "Sexta": 5 };
        const diaAlvo = mapaDias[diaNome];
        const hoje = new Date();
        const diaAtual = hoje.getDay();

        let diferenca = diaAlvo - diaAtual;
        if (diferenca <= 0) {
            diferenca += 7;
        }

        const dataAlvo = new Date(hoje);
        dataAlvo.setDate(hoje.getDate() + diferenca);
        return dataAlvo;
    }

    function formatarDataISO(dataObj) {
        const ano = dataObj.getFullYear();
        const mes = String(dataObj.getMonth() + 1).padStart(2, '0');
        const dia = String(dataObj.getDate()).padStart(2, '0');
        return `${ano}-${mes}-${dia}`;
    }

    function formatarDataBR(dataObj) {
        const dia = String(dataObj.getDate()).padStart(2, '0');
        const mes = String(dataObj.getMonth() + 1).padStart(2, '0');
        return `${dia}/${mes}`;
    }

    function atualizarDatasNoCabecalho() {
        dias.forEach(dia => {
            const dataObj = obterDataDoDiaDaSemana(dia);
            const elementoData = document.getElementById(`data-${dia}`);
            if (elementoData) {
                elementoData.textContent = `(${formatarDataBR(dataObj)})`;
            }
        });
    }

    async function carregarGrade() {
        try {
            const resposta = await fetch("/api/grade");
            const resultado = await resposta.json();
            dadosGlobais = resultado.grade;
            reservasGlobais = resultado.reservas;
            atualizarDatasNoCabecalho();
            renderizarTabela();
        } catch (erro) {
            console.error("Erro ao carregar a grade:", erro);
        }
    }

    function renderizarTabela() {
        tabelaCorpo.innerHTML = "";
        const labSelecionado = selectLab.value;
        const horarios = Object.keys(dadosGlobais["Segunda"]?.[labSelecionado] || {});

        horarios.forEach(horario => {
            const tr = document.createElement("tr");

            const tdHorario = document.createElement("td");
            tdHorario.textContent = horario;
            tr.appendChild(tdHorario);

            dias.forEach(dia => {
                const td = document.createElement("td");
                const dataObj = obterDataDoDiaDaSemana(dia);
                const dataISO = formatarDataISO(dataObj);

                const aulaFixa = dadosGlobais[dia]?.[labSelecionado]?.[horario] || "LIVRE";
                const chaveSlot = `${dataISO}_${labSelecionado}_${horario}`;
                const reservaDinamica = reservasGlobais[chaveSlot];

                if (reservaDinamica) {
                    td.textContent = `Reservado: ${reservaDinamica.professor} (Clique p/ cancelar)`;
                    td.className = "ocupado_reserva";
                    td.style.cursor = "pointer";
                    td.onclick = () => abrirModalCancelar(chaveSlot, reservaDinamica, formatarDataBR(dataObj));
                } else if (aulaFixa !== "LIVRE") {
                    td.textContent = aulaFixa;
                    td.className = "ocupado";
                } else {
                    td.textContent = "LIVRE";
                    td.className = "livre";
                    td.style.cursor = "pointer";
                    td.onclick = () => abrirModalReserva(dia, labSelecionado, horario, dataObj);
                }

                tr.appendChild(td);
            });

            tabelaCorpo.appendChild(tr);
        });
    }

    function abrirModalReserva(dia, laboratorio, horario, dataObj) {
        const dataISO = formatarDataISO(dataObj);
        const dataBR = formatarDataBR(dataObj);

        slotSelecionado = { dia, laboratorio, horario, dataISO };
        infoSlot.textContent = `${laboratorio} - ${dia} (${dataBR}) às ${horario}`;
        modalReserva.style.display = "block";
    }

    function abrirModalCancelar(chaveSlot, reserva, dataBR) {
        slotParaCancelar = chaveSlot;
        infoSlotCancelar.textContent = `${reserva.laboratorio} - ${reserva.dia} (${dataBR}) às ${reserva.horario} (Prof. ${reserva.professor})`;
        document.getElementById("matricula-cancelar").value = "";
        modalCancelar.style.display = "block";
    }

    fecharModalBtn.onclick = () => { modalReserva.style.display = "none"; };
    fecharModalCancelarBtn.onclick = () => { modalCancelar.style.display = "none"; };

    formReserva.onsubmit = async (e) => {
        e.preventDefault();
        const matricula = document.getElementById("matricula-professor").value.trim();

        if (!matricula) {
            alert("Por favor, digite a matrícula do professor.");
            return;
        }

        const payload = {
            dia: slotSelecionado.dia,
            laboratorio: slotSelecionado.laboratorio,
            horario: slotSelecionado.horario,
            matricula: matricula,
            data: slotSelecionado.dataISO
        };

        const btnSubmit = formReserva.querySelector('button[type="submit"]');
        btnSubmit.disabled = true;

        try {
            const resposta = await fetch("/api/reservar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const resultado = await resposta.json();
            alert(resultado.mensagem);

            if (resultado.sucesso) {
                modalReserva.style.display = "none";
                formReserva.reset();
                await carregarGrade();
            }
        } catch (erro) {
            alert("Ocorreu um erro ao processar a reserva.");
        } finally {
            btnSubmit.disabled = false;
        }
    };

    formCancelar.onsubmit = async (e) => {
        e.preventDefault();
        const matricula = document.getElementById("matricula-cancelar").value.trim();

        if (!matricula) {
            alert("Digite a matrícula do professor responsável.");
            return;
        }

        const payload = {
            chave_slot: slotParaCancelar,
            matricula: matricula
        };

        try {
            const resposta = await fetch("/api/cancelar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const resultado = await resposta.json();
            alert(resultado.mensagem);

            if (resultado.sucesso) {
                modalCancelar.style.display = "none";
                formCancelar.reset();
                await carregarGrade();
            }
        } catch (erro) {
            alert("Erro ao processar cancelamento.");
        }
    };

    selectLab.onchange = renderizarTabela;
    carregarGrade();
});
