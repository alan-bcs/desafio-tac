"""Painel de Gerenciamento do RU — uso interno da equipe.

Acesso restrito à rede interna. Permite consultar dados de operadores
cadastrados na API administrativa para verificação de turnos e perfis.
"""

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

ADMIN_API_URL = "http://127.0.0.1:9090"
TIMEOUT_REQUISICAO = 5


@app.route("/", methods=["GET"])
def index():
    return render_template("painel.html", resultado=None, operador_id="")


@app.route("/consultar-operador", methods=["POST"])
def consultar_operador():
    operador_id = request.form.get("operador_id", "").strip()

    if not operador_id:
        return render_template(
            "painel.html",
            resultado="Informe o ID do operador para consultar.",
            operador_id=operador_id,
        )

    try:
        resposta = requests.get(
            f"{ADMIN_API_URL}/api/v1/operadores/{operador_id}",
            timeout=TIMEOUT_REQUISICAO,
        )
        if resposta.status_code == 404:
            resultado = f"Operador com ID {operador_id} não encontrado."
        else:
            resultado = f"HTTP {resposta.status_code}\n\n{resposta.text}"
    except requests.RequestException as erro:
        resultado = f"Falha ao consultar operador: {erro}"

    return render_template(
        "painel.html", resultado=resultado, operador_id=operador_id
    )


@app.route("/healthz", methods=["GET"])
def healthz():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
