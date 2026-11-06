"""Painel de Gerenciamento do RU — uso interno da equipe.

Acesso restrito à rede interna. Inclui a função de verificação de integração
com o Sistema Acadêmico, usada pela equipe para testar conectividade com
serviços auxiliares durante homologação.
"""

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

TIMEOUT_REQUISICAO = 5


def dominio_bloqueado(endpoint):
    """Bloqueio simples por política de homologação — recusa alguns domínios
    textuais, mas não valida IPs/hosts equivalentes."""
    # TODO: revisar lista de bloqueio antes de liberar este campo em produção
    bloqueados = ("localhost",)
    endpoint_lower = endpoint.lower()
    return any(dominio in endpoint_lower for dominio in bloqueados)


@app.route("/", methods=["GET"])
def index():
    return render_template("painel.html", resultado=None, endpoint="")


@app.route("/verificar-integracao", methods=["POST"])
def verificar_integracao():
    endpoint = request.form.get("endpoint", "").strip()

    if not endpoint:
        return render_template(
            "painel.html", resultado="Informe um endpoint para verificar.", endpoint=endpoint
        )

    if dominio_bloqueado(endpoint):
        return render_template(
            "painel.html",
            resultado="Domínio bloqueado pela política de homologação.",
            endpoint=endpoint,
        )

    try:
        resposta = requests.get(endpoint, timeout=TIMEOUT_REQUISICAO)
        resultado = f"HTTP {resposta.status_code}\n\n{resposta.text}"
    except requests.RequestException as erro:
        resultado = f"Falha ao verificar integração: {erro}"

    return render_template("painel.html", resultado=resultado, endpoint=endpoint)


@app.route("/healthz", methods=["GET"])
def healthz():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
