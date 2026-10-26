import csv
import json
import os
import threading
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, current_app
from flask_mail import Mail, Message
from dotenv import load_dotenv  

load_dotenv()

app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
app.config['MAIL_DEFAULT_SENDER'] = ('Reserva de Laboratórios', app.config['MAIL_USERNAME'])

mail = Mail(app)

ARQUIVO_CSV = "grade_horaria.csv"
ARQUIVO_RESERVAS = "reservas.json"
ARQUIVO_USUARIOS = "usuarios.csv"


def enviar_email_async(app_ctx, msg):
    with app_ctx.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")


def disparar_email(assunto, destinatario, corpo):
    msg = Message(assunto, recipients=[destinatario])
    msg.body = corpo
    threading.Thread(target=enviar_email_async, args=(current_app._get_current_object(), msg)).start()


def carregar_usuarios():
    usuarios = {}
    if not os.path.exists(ARQUIVO_USUARIOS):
        return usuarios

    with open(ARQUIVO_USUARIOS, mode="r", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        for linha in leitor:
            matricula = linha["matricula"].strip()
            usuarios[matricula] = {
                "nome": linha["nome"].strip(),
                "funcao": linha["funcao"].strip(),
                "email": linha["email"].strip()
            }
    return usuarios


def carregar_grade_csv():
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


grade_escolar = carregar_grade_csv()


def carregar_reservas():
    if os.path.exists(ARQUIVO_RESERVAS):
        try:
            with open(ARQUIVO_RESERVAS, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def salvar_reservas(reservas):
    with open(ARQUIVO_RESERVAS, "w", encoding="utf-8") as f:
        json.dump(reservas, f, ensure_ascii=False, indent=4)


def limpar_reservas_expiradas():
    reservas = carregar_reservas()
    hoje = datetime.now().date()
    reservas_filtradas = {}
    mudou = False

    for chave, dados in reservas.items():
        try:
            data_reserva = datetime.strptime(dados["data"], "%Y-%m-%d").date()
            if data_reserva >= hoje:
                reservas_filtradas[chave] = dados
            else:
                mudou = True
        except (KeyError, ValueError):
            mudou = True

    if mudou:
        salvar_reservas(reservas_filtradas)
    return reservas_filtradas


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/grade", methods=["GET"])
def obter_grade():
    reservas_validas = limpar_reservas_expiradas()
    return jsonify({"grade": grade_escolar, "reservas": reservas_validas})


@app.route("/api/reservar", methods=["POST"])
def fazer_reserva():
    dados = request.json or {}
    dia = dados.get("dia")
    laboratorio = dados.get("laboratorio")
    horario = dados.get("horario")
    matricula = str(dados.get("matricula", "")).strip().upper()
    data_desejada_str = dados.get("data")

    if not all([dia, laboratorio, horario, matricula, data_desejada_str]):
        return jsonify({"sucesso": False, "mensagem": "Preencha todos os campos obrigatórios."}), 400

    usuarios = carregar_usuarios()
    if matricula not in usuarios:
        return jsonify({"sucesso": False, "mensagem": "Matrícula não cadastrada no sistema."}), 403

    usuario = usuarios[matricula]

    if usuario["funcao"].lower() != "professor" and usuario["funcao"].lower() != "admin":
        return jsonify({"sucesso": False, "mensagem": "Apenas professores podem efetuar reservas."}), 403

    nome_professor = usuario["nome"]
    email_professor = usuario["email"]

    try:
        data_desejada = datetime.strptime(data_desejada_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"sucesso": False, "mensagem": "Formato de data inválido."}), 400

    hoje = datetime.now().date()
    amanha = hoje + timedelta(days=1)
    limite_maximo = hoje + timedelta(days=7)

    if not (amanha <= data_desejada <= limite_maximo):
        return jsonify({"sucesso": False, "mensagem": "As reservas devem ser feitas de amanhã até 7 dias."}), 400

    if grade_escolar.get(dia, {}).get(laboratorio, {}).get(horario, "LIVRE") != "LIVRE":
        return jsonify({"sucesso": False, "mensagem": "Este horário possui aula fixa."}), 400

    reservas = limpar_reservas_expiradas()
    chave_slot = f"{data_desejada_str}_{laboratorio}_{horario}"

    if chave_slot in reservas:
        return jsonify({"sucesso": False, "mensagem": "O laboratório já se encontra reservado para este horário."}), 400

    reservas[chave_slot] = {
        "professor": nome_professor,
        "matricula": matricula,
        "email": email_professor,
        "data": data_desejada_str,
        "laboratorio": laboratorio,
        "horario": horario,
        "dia": dia
    }
    salvar_reservas(reservas)

    if email_professor:
        corpo = (
            f"Olá Prof. {nome_professor},\n\n"
            f"A sua reserva foi efetuada com sucesso!\n\n"
            f"• Laboratório: {laboratorio}\n"
            f"• Dia da semana: {dia}\n"
            f"• Data: {data_desejada_str}\n"
            f"• Horário: {horario}\n\n"
            f"Caso precise cancelar, utilize a sua matrícula no sistema."
        )
        #disparar_email("Confirmação de Reserva de Laboratório", email_professor, corpo)

    return jsonify({"sucesso": True, "mensagem": f"Reserva efetuada com sucesso para {nome_professor}!"})


@app.route("/api/cancelar", methods=["POST"])
def cancelar_reserva():
    dados = request.json or {}
    chave_slot = dados.get("chave_slot")
    matricula_informada = str(dados.get("matricula", "")).strip().upper()

    if not chave_slot or not matricula_informada:
        return jsonify({"sucesso": False, "mensagem": "Chave de reserva e matrícula são obrigatórias."}), 400

    usuarios = carregar_usuarios()
    if matricula_informada not in usuarios:
        return jsonify({"sucesso": False, "mensagem": "Matrícula não encontrada."}), 403

    reservas = carregar_reservas()
    if chave_slot not in reservas:
        return jsonify({"sucesso": False, "mensagem": "Reserva não encontrada."}), 404

    reserva = reservas[chave_slot]

    if reserva.get("matricula") != matricula_informada:
        return jsonify({"sucesso": False, "mensagem": "Apenas o professor responsável pode cancelar esta reserva."}), 403

    del reservas[chave_slot]
    salvar_reservas(reservas)

    email_professor = reserva.get("email") or usuarios[matricula_informada].get("email")
    if email_professor:
        corpo = (
            f"Olá Prof. {reserva.get('professor')},\n\n"
            f"A sua reserva para o {reserva.get('laboratorio')} no dia {reserva.get('data')} às {reserva.get('horario')} foi CANCELADA com sucesso.\n"
        )
        #disparar_email("Cancelamento de Reserva de Laboratório", email_professor, corpo)

    return jsonify({"sucesso": True, "mensagem": "Reserva cancelada com sucesso!"})


if __name__ == "__main__":
    limpar_reservas_expiradas()
    app.run(debug=True)