from flask import Flask, request, jsonify, Response
import sqlite3
import datetime
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = 'reservas.db'

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    raise TypeError(f"Tipo nao serializavel: {type(obj)}")

@app.route('/reservas-disponiveis', methods=['GET'])
def reservas_disponiveis():
    try:
        con = conectar()
        cur = con.cursor()

        cur.execute('''
            SELECT * FROM reservas WHERE status = 'reservada'
        ''')
        rows = cur.fetchall()
        resultado = [dict(row) for row in rows]

        cur.close()
        con.close()

        return Response(json.dumps(resultado, default=converter_para_json), mimetype='application/json')
    except Exception as e:
        print(f"Erro ao buscar reservas disponiveis: {e}")
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

        cur.execute('UPDATE reservas SET status = "confirmada", garcom = ? WHERE id = ?', (garcom, id))
        con.commit()
        cur.close()
        con.close()
        return jsonify({'mensagem': 'Reserva confirmada com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
