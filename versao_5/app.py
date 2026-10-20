import csv
import json
import os
from datetime import datetime, timedelta

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

ARQUIVO_CSV = "grade_horaria.csv"
ARQUIVO_RESERVAS = "reservas.json"


def carregar_grade_csv():
    """Lê o arquivo CSV e o converte para o formato de dicionário aninhado."""
    grade = {}
    if not os.path.exists(ARQUIVO_CSV):
        return grade

    with open(ARQUIVO_CSV, mode="r", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            dia = linha["dia"]
            lab = linha["laboratorio"]
            horario = linha["horario"]
            disciplina = linha["disciplina_professor"]

            if dia not in grade:
                grade[dia] = {}
            if lab not in grade[dia]:
                grade[dia][lab] = {}

            grade[dia][lab][horario] = disciplina
    return grade


# Carrega a grade fixa a partir do CSV
grade_escolar = carregar_grade_csv()


def carregar_reservas():
    if os.path.exists(ARQUIVO_RESERVAS):
        with open(ARQUIVO_RESERVAS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_reservas(reservas):
    with open(ARQUIVO_RESERVAS, "w", encoding="utf-8") as f:
        json.dump(reservas, f, ensure_ascii=False, indent=4)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/grade", methods=["GET"])
def obter_grade():
    reservas = carregar_reservas()
    hoje = datetime.now().date()

    # Remove reservas antigas
    reservas_atualizadas = {}
    for chave, dados in reservas.items():
        data_reserva = datetime.strptime(dados["data"], "%Y-%m-%d").date()
        if data_reserva >= hoje:
            reservas_atualizadas[chave] = dados
    salvar_reservas(reservas_atualizadas)

    return jsonify({"grade": grade_escolar, "reservas": reservas_atualizadas})


@app.route("/api/reservar", methods=["POST"])
def fazer_reserva():
    dados = request.json
    dia = dados.get("dia")
    laboratorio = dados.get("laboratorio")
    horario = dados.get("horario")
    professor = dados.get("professor")
    data_desejada_str = dados.get("data")

    if not all([dia, laboratorio, horario, professor, data_desejada_str]):
        return jsonify({"sucesso": False, "mensagem": "Preencha todos os campos."})

    data_desejada = datetime.strptime(data_desejada_str, "%Y-%m-%d").date()
    hoje = datetime.now().date()

    if data_desejada > hoje + timedelta(days=7):
        return jsonify(
            {
                "sucesso": False,
                "mensagem": (
                    "A reserva deve ser feita para até 7 dias a partir de hoje"
                ),
            }
        )

    reservas = carregar_reservas()
    chave_slot = f"{dia}_{laboratorio}_{horario}"

    if grade_escolar.get(dia, {}).get(laboratorio, {}).get(horario, "LIVRE") != "LIVRE":
        return jsonify(
            {
                "sucesso": False,
                "mensagem": "Este horário possui aula fixa da grade curricular.",
            }
        )

    if chave_slot in reservas:
        return jsonify(
            {
                "sucesso": False,
                "mensagem": "Este horário já está reservado por outro professor.",
            }
        )

    reservas[chave_slot] = {
        "professor": professor,
        "data": data_desejada_str,
        "laboratorio": laboratorio,
        "horario": horario,
    }
    salvar_reservas(reservas)

    return jsonify({"sucesso": True, "mensagem": "Reserva realizada com sucesso!"})


if __name__ == "__main__":
    app.run(debug=True)
