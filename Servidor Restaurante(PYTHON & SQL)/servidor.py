from flask import Flask, request, jsonify, Response, render_template
import sqlite3
from collections import OrderedDict
import datetime
import json
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

DB_PATH = 'reservas.db'

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acessar colunas por nome (como dicionário)
    criar_tabela(conn)
    return conn

def criar_tabela(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            mesa INTEGER NOT NULL,
            pessoas INTEGER NOT NULL,
            responsavel TEXT NOT NULL,
            status TEXT DEFAULT 'reservada',
            garcom TEXT
        )
    ''')
    conn.commit()

def converter_para_json(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, datetime.time):
        return obj.strftime('%H:%M:%S')
    elif isinstance(obj, datetime.timedelta):
        total_seconds = int(obj.total_seconds())
        horas = total_seconds // 3600
        minutos = (total_seconds % 3600) // 60
        segundos = total_seconds % 60
        return f"{horas:02}:{minutos:02}:{segundos:02}"
    raise TypeError(f"Tipo não serializável: {type(obj)}")

@app.route('/')
def home():
    return render_template('atendente.html')

@app.route('/garcom')
def pagina_garcom():
    return render_template('garcom.html')

@app.route('/gerente')
def pagina_gerente():
    return render_template('gerente.html')

@app.route('/reserva', methods=['POST'])
def criar_reserva():
    dados = request.json
    try:
        data_original = dados['data']
        data_obj = datetime.datetime.strptime(data_original, '%Y-%m-%d')
        dados['data'] = data_obj.strftime('%Y-%m-%d')

        con = conectar()
        cur = con.cursor()

        cur.execute('''
            SELECT * FROM reservas
            WHERE mesa = ? AND data = ? AND hora = ? AND status = 'reservada'
        ''', (dados['mesa'], dados['data'], dados['hora']))

        if cur.fetchone():
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Mesa ja reservada nesse horario'}), 400

        cur.execute('''
            INSERT INTO reservas (data, hora, mesa, pessoas, responsavel, status)
            VALUES (?, ?, ?, ?, ?, 'reservada')
        ''', (dados['data'], dados['hora'], dados['mesa'], dados['pessoas'], dados['responsavel']))
        reserva_id = cur.lastrowid

        con.commit()
        cur.close()
        con.close()

        resposta = OrderedDict([
            ('mensagem', 'Reserva criada com sucesso'),
            ('id', reserva_id)
        ])
        return Response(json.dumps(resposta), mimetype='application/json')
    except Exception as e:
        print(f"Erro ao criar reserva: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/reserva/<int:id>', methods=['DELETE'])
def cancelar_reserva(id):
    try:
        con = conectar()
        cur = con.cursor()

        cur.execute('SELECT * FROM reservas WHERE id = ?', (id,))
        if not cur.fetchone():
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Reserva nao encontrada'}), 404

        cur.execute('DELETE FROM reservas WHERE id = ?', (id,))
        con.commit()
        cur.close()
        con.close()
        return jsonify({'mensagem': 'Reserva cancelada com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/confirmar/<int:id>', methods=['POST'])
def confirmar_reserva(id):
    garcom = request.json.get('garcom')
    if not garcom:
        return jsonify({'mensagem': 'Campo "garcom" e obrigatorio'}), 400
    try:
        con = conectar()
        cur = con.cursor()

        cur.execute('SELECT * FROM reservas WHERE id = ? AND status = "reservada"', (id,))
        if not cur.fetchone():
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Reserva nao encontrada ou ja confirmada'}), 404

        cur.execute('''
            UPDATE reservas SET status = 'confirmada', garcom = ? WHERE id = ?
        ''', (garcom, id))
        con.commit()
        cur.close()
        con.close()
        return jsonify({'mensagem': 'Reserva confirmada'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/relatorio/periodo', methods=['GET'])
def relatorio_periodo():
    inicio = request.args.get('inicio')
    fim = request.args.get('fim')

    if not inicio or not fim:
        return jsonify({'error': 'Parametros "inicio" e "fim" sao obrigatorios.'}), 400

    try:
        con = conectar()
        cur = con.cursor()
        cur.execute('''
            SELECT * FROM reservas
            WHERE data BETWEEN ? AND ?
        ''', (inicio, fim))
        rows = cur.fetchall()
        reservas = [dict(row) for row in rows]
        cur.close()
        con.close()
        return Response(json.dumps(reservas, default=converter_para_json), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/relatorio/mesa/<int:mesa>', methods=['GET'])
def relatorio_mesa(mesa):
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute('SELECT * FROM reservas WHERE mesa = ?', (mesa,))
        rows = cur.fetchall()
        resultado = [dict(row) for row in rows]
        cur.close()
        con.close()
        return Response(json.dumps(resultado, default=converter_para_json), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/relatorio/garcom/<string:nome>', methods=['GET'])
def relatorio_garcom(nome):
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute('SELECT * FROM reservas WHERE garcom = ?', (nome,))
        rows = cur.fetchall()
        resultado = [dict(row) for row in rows]
        cur.close()
        con.close()
        return Response(json.dumps(resultado, default=converter_para_json), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reservas-disponiveis', methods=['GET'])
def listar_reservas_disponiveis():
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute("SELECT id, data, hora, mesa, pessoas, responsavel FROM reservas WHERE status = 'reservada' ORDER BY data, hora")
        rows = cur.fetchall()
        reservas = [dict(row) for row in rows]
        cur.close()
        con.close()
        return Response(json.dumps(reservas, default=converter_para_json), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
