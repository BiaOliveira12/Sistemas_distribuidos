from flask import Flask, request, jsonify, Response, render_template
import sqlite3
from collections import OrderedDict
import datetime
import json
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

DB_PATH = 'reservas.db'

def calcular_hora_fim(hora_inicio):
    """Calcula a hora de fim adicionando 1 hora à hora de início"""
    try:
        hora_obj = datetime.datetime.strptime(hora_inicio, '%H:%M').time()
        hora_datetime = datetime.datetime.combine(datetime.date.today(), hora_obj)
        hora_fim = hora_datetime + datetime.timedelta(hours=1)
        return hora_fim.strftime('%H:%M')
    except:
        return None

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  
    criar_tabela(conn)
    return conn

def criar_tabela(conn):
    cursor = conn.cursor()
    
    # Criar tabela principal se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            mesa INTEGER NOT NULL,
            pessoas INTEGER NOT NULL,
            responsavel TEXT NOT NULL,
            status TEXT DEFAULT 'reservada',
            garcom TEXT,
            hora_fim TEXT,
            data_confirmacao TEXT,
            hora_confirmacao TEXT
        )
    ''')
    
    # Verificar se as novas colunas existem e adicionar se necessário
    cursor.execute("PRAGMA table_info(reservas)")
    colunas_existentes = [coluna[1] for coluna in cursor.fetchall()]
    
    if 'hora_fim' not in colunas_existentes:
        cursor.execute('ALTER TABLE reservas ADD COLUMN hora_fim TEXT')
        print("[INFO] Coluna 'hora_fim' adicionada à tabela")
        
    if 'data_confirmacao' not in colunas_existentes:
        cursor.execute('ALTER TABLE reservas ADD COLUMN data_confirmacao TEXT')
        print("[INFO] Coluna 'data_confirmacao' adicionada à tabela")
        
    if 'hora_confirmacao' not in colunas_existentes:
        cursor.execute('ALTER TABLE reservas ADD COLUMN hora_confirmacao TEXT')
        print("[INFO] Coluna 'hora_confirmacao' adicionada à tabela")
    
    # Atualizar reservas existentes que não têm hora_fim calculada
    cursor.execute('''
        SELECT id, hora FROM reservas 
        WHERE hora_fim IS NULL AND hora IS NOT NULL
    ''')
    reservas_sem_fim = cursor.fetchall()
    
    for reserva in reservas_sem_fim:
        hora_fim = calcular_hora_fim(reserva[1])
        if hora_fim:
            cursor.execute('UPDATE reservas SET hora_fim = ? WHERE id = ?', (hora_fim, reserva[0]))
            print(f"[INFO] Hora fim calculada para reserva ID {reserva[0]}: {reserva[1]} -> {hora_fim}")
    
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

def verificar_conflito_horario(mesa, data, hora_inicio, reserva_id=None):
    """Verifica se há conflito de horário para uma mesa em uma data específica"""
    try:
        con = conectar()
        cur = con.cursor()
        
        # Buscar todas as reservas confirmadas da mesa na data específica
        query = '''
            SELECT id, hora, hora_fim, status FROM reservas 
            WHERE mesa = ? AND data = ? AND status = 'confirmada'
        '''
        params = [mesa, data]
        
        # Se estiver editando uma reserva, excluir ela da verificação
        if reserva_id:
            query += ' AND id != ?'
            params.append(reserva_id)
            
        cur.execute(query, params)
        reservas_existentes = cur.fetchall()
        cur.close()
        con.close()
        
        print(f"[DEBUG] Verificando conflito para mesa {mesa}, data {data}, hora {hora_inicio}")
        print(f"[DEBUG] Reservas confirmadas encontradas: {len(reservas_existentes)}")
        
        if not reservas_existentes:
            print("[DEBUG] Nenhuma reserva confirmada encontrada - OK")
            return False
        
        # Calcular horário de fim da nova reserva
        hora_fim_nova = calcular_hora_fim(hora_inicio)
        print(f"[DEBUG] Nova reserva: {hora_inicio} até {hora_fim_nova}")
        
        # Converter para datetime para comparação
        try:
            hora_inicio_obj = datetime.datetime.strptime(hora_inicio, '%H:%M').time()
            hora_fim_obj = datetime.datetime.strptime(hora_fim_nova, '%H:%M').time()
        except Exception as e:
            print(f"[DEBUG] Erro ao converter horários: {e}")
            return True
        
        # Verificar conflitos com reservas existentes
        for reserva in reservas_existentes:
            print(f"[DEBUG] Verificando contra reserva ID {reserva['id']}: {reserva['hora']} até {reserva['hora_fim']}")
            
            try:
                reserva_inicio = datetime.datetime.strptime(reserva['hora'], '%H:%M').time()
                reserva_fim = datetime.datetime.strptime(reserva['hora_fim'], '%H:%M').time()
                
                # Verificar sobreposição de horários
                # Há conflito se: nova_inicio < reserva_fim E nova_fim > reserva_inicio
                if (hora_inicio_obj < reserva_fim and hora_fim_obj > reserva_inicio):
                    print(f"[DEBUG] CONFLITO DETECTADO! Nova reserva {hora_inicio_obj}-{hora_fim_obj} sobrepõe com {reserva_inicio}-{reserva_fim}")
                    return True
                else:
                    print(f"[DEBUG] Sem conflito com esta reserva")
                    
            except Exception as e:
                print(f"[DEBUG] Erro ao processar reserva {reserva['id']}: {e}")
                return True
                
        print("[DEBUG] Nenhum conflito encontrado - OK")
        return False
        
    except Exception as e:
        print(f"[DEBUG] Erro geral ao verificar conflito: {e}")
        return True  # Em caso de erro, considerar que há conflito por segurança

# ROTAS CORRIGIDAS - mantendo os endereços originais
@app.route('/')
def home():
    """Página inicial (index)"""
    return render_template('index.html')

@app.route('/atendente')
def pagina_atendente():
    """Página do atendente"""
    return render_template('atendente.html')

@app.route('/garcom')
def pagina_garcom():
    """Página do garçom"""
    return render_template('garcom.html')

@app.route('/gerente')
def pagina_gerente():
    """Página do gerente"""
    return render_template('gerente.html')

@app.route('/reserva', methods=['POST'])
def criar_reserva():
    dados = request.json
    try:
        # Verificar se a mesa está no range válido (1-20)
        if dados['mesa'] > 20 or dados['mesa'] < 1:
            return jsonify({'mensagem': 'Mesa deve estar entre 1 e 20'}), 400

        # Verificar se não é uma data/hora passada
        data_obj = datetime.datetime.strptime(dados['data'], '%Y-%m-%d')
        hora_obj = datetime.datetime.strptime(dados['hora'], '%H:%M').time()
        data_hora_reserva = datetime.datetime.combine(data_obj.date(), hora_obj)
        
        if data_hora_reserva <= datetime.datetime.now():
            return jsonify({'mensagem': 'Não é possível fazer reservas para datas/horas passadas'}), 400

        dados['data'] = data_obj.strftime('%Y-%m-%d')
        
        # Calcular hora de fim (1 hora depois)
        hora_fim = calcular_hora_fim(dados['hora'])
        if not hora_fim:
            return jsonify({'mensagem': 'Formato de hora inválido'}), 400

        con = conectar()
        cur = con.cursor()

        # Verificar se a mesa já está reservada no horário exato (apenas para reservas não confirmadas)
        cur.execute('''
            SELECT * FROM reservas
            WHERE mesa = ? AND data = ? AND hora = ? AND status = 'reservada'
        ''', (dados['mesa'], dados['data'], dados['hora']))

        if cur.fetchone():
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Mesa ja reservada nesse horario'}), 400

        # Verificar conflito com reservas confirmadas (mesa em uso)
        if verificar_conflito_horario(dados['mesa'], dados['data'], dados['hora']):
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Mesa em uso nesse horario'}), 400

        cur.execute('''
            INSERT INTO reservas (data, hora, mesa, pessoas, responsavel, status, hora_fim)
            VALUES (?, ?, ?, ?, ?, 'reservada', ?)
        ''', (dados['data'], dados['hora'], dados['mesa'], dados['pessoas'], dados['responsavel'], hora_fim))
        reserva_id = cur.lastrowid

        con.commit()
        cur.close()
        con.close()

        resposta = OrderedDict([
            ('mensagem', 'Reserva criada com sucesso'),
            ('id', reserva_id),
            ('hora_fim', hora_fim)
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

        # Verificar se a reserva existe e verificar status
        cur.execute('SELECT status FROM reservas WHERE id = ?', (id,))
        reserva = cur.fetchone()
        
        if not reserva:
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Reserva nao encontrada'}), 404

        # Verificar se a reserva já foi confirmada
        if reserva['status'] == 'confirmada':
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Nao e possivel cancelar reserva ja confirmada pelo garcom'}), 400

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

        # Buscar a reserva
        cur.execute('SELECT * FROM reservas WHERE id = ? AND status = "reservada"', (id,))
        reserva = cur.fetchone()
        if not reserva:
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Reserva nao encontrada ou ja confirmada'}), 404

        # Verificar novamente se há conflito no momento da confirmação
        if verificar_conflito_horario(reserva['mesa'], reserva['data'], reserva['hora'], id):
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Mesa em uso nesse horario'}), 400

        # Registrar data e hora da confirmação
        agora = datetime.datetime.now()
        data_confirmacao = agora.strftime('%Y-%m-%d')
        hora_confirmacao = agora.strftime('%H:%M')

        cur.execute('''
            UPDATE reservas SET status = 'confirmada', garcom = ?, 
            data_confirmacao = ?, hora_confirmacao = ?
            WHERE id = ?
        ''', (garcom, data_confirmacao, hora_confirmacao, id))
        con.commit()
        cur.close()
        con.close()
        return jsonify({
            'mensagem': 'Reserva confirmada',
            'horario_fim': reserva['hora_fim']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/finalizar/<int:id>', methods=['POST'])
def finalizar_reserva(id):
    """Nova rota para finalizar uma reserva manualmente"""
    try:
        con = conectar()
        cur = con.cursor()

        cur.execute('SELECT * FROM reservas WHERE id = ? AND status = "confirmada"', (id,))
        if not cur.fetchone():
            cur.close()
            con.close()
            return jsonify({'mensagem': 'Reserva nao encontrada ou nao confirmada'}), 404

        cur.execute('UPDATE reservas SET status = "finalizada" WHERE id = ?', (id,))
        con.commit()
        cur.close()
        con.close()
        return jsonify({'mensagem': 'Reserva finalizada com sucesso'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/mesa/<int:mesa>/disponibilidade', methods=['GET'])
def verificar_disponibilidade_mesa(mesa):
    """Verifica a disponibilidade de uma mesa em uma data específica"""
    data = request.args.get('data')
    if not data:
        return jsonify({'error': 'Parametro "data" e obrigatorio'}), 400
        
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute('''
            SELECT hora, hora_fim, status, responsavel FROM reservas 
            WHERE mesa = ? AND data = ? AND status IN ('reservada', 'confirmada')
            ORDER BY hora
        ''', (mesa, data))
        reservas = cur.fetchall()
        cur.close()
        con.close()
        
        horarios_ocupados = []
        for reserva in reservas:
            horarios_ocupados.append({
                'hora_inicio': reserva['hora'],
                'hora_fim': reserva['hora_fim'],
                'status': reserva['status'],
                'responsavel': reserva['responsavel']
            })
            
        return Response(json.dumps({
            'mesa': mesa,
            'data': data,
            'horarios_ocupados': horarios_ocupados
        }, default=converter_para_json), mimetype='application/json')
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

@app.route('/mesas-em-uso', methods=['GET'])
def listar_mesas_em_uso():
    """Lista todas as mesas que estão sendo usadas no momento"""
    try:
        con = conectar()
        cur = con.cursor()
        agora = datetime.datetime.now()
        data_atual = agora.strftime('%Y-%m-%d')
        hora_atual = agora.strftime('%H:%M')
        
        cur.execute('''
            SELECT id, mesa, hora, hora_fim, responsavel, garcom 
            FROM reservas 
            WHERE status = 'confirmada' 
            AND data = ? 
            AND hora <= ? 
            AND hora_fim > ?
            ORDER BY mesa
        ''', (data_atual, hora_atual, hora_atual))
        
        rows = cur.fetchall()
        mesas_em_uso = [dict(row) for row in rows]
        cur.close()
        con.close()
        
        return Response(json.dumps(mesas_em_uso, default=converter_para_json), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/reservas', methods=['GET'])
def debug_reservas():
    """Rota para debug - mostra todas as reservas com detalhes"""
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute('SELECT * FROM reservas ORDER BY data, hora')
        rows = cur.fetchall()
        cur.close()
        con.close()
        
        reservas = []
        for row in rows:
            reserva = dict(row)
            # Se não tem hora_fim calculada, calcular agora
            if not reserva.get('hora_fim') and reserva.get('hora'):
                reserva['hora_fim'] = calcular_hora_fim(reserva['hora'])
            reservas.append(reserva)
        
        return Response(json.dumps(reservas, default=converter_para_json, indent=2), mimetype='application/json')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)