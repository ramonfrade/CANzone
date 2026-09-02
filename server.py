import random
import time
from flask import Flask, jsonify, request, render_template_string, session
import json

server = Flask(__name__)
server.secret_key = "chave_secreta_telemetria"  # Necessário para gerenciar sessões

SENHA_ACESSO = "123456"

with open("index.html", "r", encoding="utf-8") as file:
    HTML_PAGE = file.read()

@server.route("/")
def index():
    return render_template_string(HTML_PAGE)

@server.route("/api/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    if data.get("password") == SENHA_ACESSO:
        session["autenticado"] = True
        return jsonify({"status": "sucesso"})
    return jsonify({"erro": "Senha incorreta"}), 401

@server.route("/api/telemetria")
def get_telemetry():
    # 1. Verifica se o usuário está autenticado
    if not session.get("autenticado"):
        return jsonify({"erro": "Acesso não autorizado"}), 401

    nome_arquivo = "telemetry.json"
    # 2. Tenta ler o arquivo JSON salvo
    try:
        with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
            # Transforma o texto do JSON de volta em um dicionário Python
            dados_veiculo = json.load(arquivo)

            print(dados_veiculo)
            
        # 3. Retorna os dados lidos para o usuário
        return jsonify(dados_veiculo), 200

    except FileNotFoundError:
        # Caso o arquivo ainda não tenha sido criado/salvo
        return jsonify({"erro": f"Arquivo '{nome_arquivo}' não encontrado."}), 404
    except json.JSONDecodeError:
        # Caso o arquivo esteja corrompido ou mal formatado
        return jsonify({"erro": "Erro ao ler a estrutura do arquivo de telemetria."}), 500
    
if __name__ == "__main__":
    server.run(host="0.0.0.0", debug=True, port=5000)
