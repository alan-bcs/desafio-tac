"""API interna de gerenciamento de operadores.

Nunca pensada para ser exposta fora da rede interna do container — por isso não
tem autenticação. Usada por outros serviços internos para consultar dados de
operadores do caixa do RU.
"""

import os

from flask import Flask, abort, jsonify

DADOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")

app = Flask(__name__)

# Cadastro interno de operadores do RU — mantido em memória para simplicidade.
# TODO: migrar para banco quando o time de infra liberar o PostgreSQL interno.
OPERADORES = [
    {
        "id": 1,
        "usuario": "ana_atendimento",
        "nome": "Ana Paula Souza",
        "cargo": "Atendente de Balcão",
        "email": "ana.souza@ru.unb.br",
        "chave_privada": None,
    },
    {
        "id": 2,
        "usuario": "carlos_supervisao",
        "nome": "Carlos Eduardo Lima",
        "cargo": "Supervisor de Turno",
        "email": "carlos.lima@ru.unb.br",
        "chave_privada": None,
    },
    {
        "id": 3,
        "usuario": "operador_caixa",
        "nome": "Sistema Operador de Caixa",
        "cargo": "Operador de Caixa (automação)",
        "email": "operador_caixa@ru.unb.br",
        "chave_privada": "chave_operador_caixa.pem",
    },
]


def _buscar_operador(operador_id):
    for op in OPERADORES:
        if op["id"] == operador_id:
            return op
    return None


def _ler_chave_ssh(nome_arquivo):
    caminho = os.path.join(DADOS_DIR, nome_arquivo)
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()


def _serializar_operador(operador):
    """Retorna o operador com a chave privada resolvida (lida do disco)."""
    dados = dict(operador)
    if dados["chave_privada"] is not None:
        dados["chave_privada"] = _ler_chave_ssh(dados["chave_privada"])
    return dados


@app.route("/api/v1/operadores", methods=["GET"])
def listar_operadores():
    resumo = [
        {"id": op["id"], "usuario": op["usuario"], "cargo": op["cargo"]}
        for op in OPERADORES
    ]
    return jsonify(resumo)


@app.route("/api/v1/operadores/<int:op_id>", methods=["GET"])
def obter_operador(op_id):
    operador = _buscar_operador(op_id)
    if operador is None:
        abort(404)
    return jsonify(_serializar_operador(operador))


@app.route("/healthz", methods=["GET"])
def healthz():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9090)
