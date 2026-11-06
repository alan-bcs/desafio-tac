"""API interna de gerenciamento de operadores.

Nunca pensada para ser exposta fora da rede interna do container — por isso não
tem autenticação. Usada por outros serviços internos para consultar dados de
operadores do caixa do RU.
"""

import os

from flask import Flask, jsonify

CHAVE_OPERADOR_CAIXA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dados", "chave_operador_caixa.pem"
)

app = Flask(__name__)


def ler_chave_operador_caixa():
    with open(CHAVE_OPERADOR_CAIXA, "r", encoding="utf-8") as arquivo:
        return arquivo.read()


@app.route("/admin/credenciais", methods=["GET"])
def credenciais():
    return jsonify({
        "operador_caixa": {
            "usuario": "operador_caixa",
            "chave_privada": ler_chave_operador_caixa(),
        }
    })


@app.route("/healthz", methods=["GET"])
def healthz():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
