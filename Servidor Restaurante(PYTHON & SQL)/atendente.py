import requests
from datetime import datetime

print("1 - Criar reserva")
print("2 - Cancelar reserva")
op = input("Opção: ")

if op == '1':
    data_input = input("Data (DD-MM-YYYY): ")
    try:
        data_iso = datetime.strptime(data_input, '%d-%m-%Y').strftime('%Y-%m-%d')
    except ValueError:
        print("Data inválida")
        exit()

    dados = {
        'data': data_iso,
        'hora': input("Hora (HH:MM): "),
        'mesa': int(input("Mesa: ")),
        'pessoas': int(input("Quantidade de pessoas: ")),
        'responsavel': input("Nome do responsável: ")
    }
    r = requests.post('http://localhost:5000/reserva', json=dados)

    print("Status Code:", r.status_code)
    if r.status_code == 200 and r.text.strip():
        print(r.json())
    else:
        print("Erro ou resposta vazia:", r.text)

elif op == '2':
    id_reserva = input("ID da reserva: ")
    r = requests.delete(f'http://localhost:5000/reserva/{id_reserva}')

    print("Status Code:", r.status_code)
    if r.status_code == 200 and r.text.strip():
        print(r.json())
    else:
        print("Erro ou resposta vazia:", r.text)
