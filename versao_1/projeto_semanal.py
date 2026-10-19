from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agendamento.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = (
    'trabalhodepython@gmail.com'  # E-mail que vai enviar as mensagens
)
app.config['MAIL_PASSWORD'] = (
    'sua_senha_de_app'  # Senha de aplicativo gerada no e-mail
)
app.config['MAIL_DEFAULT_SENDER'] = 'trabalhodepython@gmail.com'

db = SQLAlchemy(app)

class Agendamento(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  dia_semana = db.Column(db.String(10), nullable=False)
  tempo = db.Column(db.Integer, nullable=False)
  professor_nome = db.Column(db.String(100), nullable=False)
  materia_ou_motivo = db.Column(db.String(100), nullable=False)

  __table_args__ = (
      db.UniqueConstraint('dia_semana', 'tempo', name='_dia_tempo_uc'),
  )

dias = ["segunda", "terça", "quarta", "quinta", "sexta"]
tempos = list(range(1,8))

@app.route('/')
def index():
  agendamentos_raw = Agendamento.query.all()
  agendamentos = {
      (a.dia_semana, a.tempo): a.professor_nome for a in agendamentos_raw
  }
  return render_template(
      'index.html', dias=dias, tempos=tempos, agendamentos=agendamentos
  )


@app.route('/agendar', methods=['POST'])
def agendar():
  dia = request.form.get('dia_semana')
  tempo = int(request.form.get('tempo'))
  professor = request.form.get('professor_nome')
  motivo = request.form.get('motivo')

  existente = Agendamento.query.filter_by(
      dia_semana=dia, tempo=tempo
  ).first()
  if not existente:
    novo_agendamento = Agendamento(
        dia_semana=dia,
        tempo=tempo,
        professor_nome=professor,
        materia_ou_motivo=motivo,
    )
    db.session.add(novo_agendamento)
    db.session.commit()

  return redirect(url_for('index'))


# Cria as tabelas automaticamente antes de rodar o app
if __name__ == '__main__':
  with app.app_context():
    db.create_all()
  app.run(debug=True)