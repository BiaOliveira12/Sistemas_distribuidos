from datetime import datetime
import requests

def get_json_safe(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            try:
                return r.json()
            except ValueError:
                print("Erro: Resposta nao e JSON valido.")
                print(f"Resposta recebida: {r.text}")
                return []
        else:
            print(f"Erro: Status {r.status_code}")
            print(f"Resposta: {r.text}")
            return []
    except requests.RequestException as e:
        print(f"Erro na requisição: {e}")
        return []

def formatar_data(data_str):
    return datetime.strptime(data_str, "%d-%m-%Y").strftime("%Y-%m-%d")

print("1 - Relatório por período")
print("2 - Relatório por mesa")
print("3 - Relatório por garçom")
op = input("Opção: ")

if op == '1':
    inicio = input("Data inicio (DD-MM-YYYY): ")
    fim = input("Data fim (DD-MM-YYYY): ")
    inicio_formatado = formatar_data(inicio)
    fim_formatado = formatar_data(fim)
    data = get_json_safe(f'http://localhost:5000/relatorio/periodo?inicio={inicio_formatado}&fim={fim_formatado}')
    for res in data:
        print(res)

elif op == '2':
    mesa = input("Número da mesa: ")
    data = get_json_safe(f'http://localhost:5000/relatorio/mesa/{mesa}')
    for res in data:
        print(res)

elif op == '3':
    nome = input("Nome do garçom: ")
    data = get_json_safe(f'http://localhost:5000/relatorio/garcom/{nome}')
    for res in data:
        print(res)
