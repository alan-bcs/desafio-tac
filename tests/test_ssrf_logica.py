"""Teste de camada 1 (lógica isolada, fora do Flask do painel): sobe a
admin-api como processo real e confirma, com `requests.get()` puro, que
`/admin/credenciais` devolve a credencial do operador_caixa sem autenticação.
"""

import os
import subprocess
import sys
import time

import requests

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_API_DIR = os.path.join(TESTS_DIR, "..", "services", "admin-api")
ADMIN_API_PORT = 9090


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
    processo = subir_admin_api()
    try:
        resposta = requests.get(f"http://127.0.0.1:{ADMIN_API_PORT}/admin/credenciais", timeout=5)
        assert resposta.status_code == 200, f"status inesperado: {resposta.status_code}"

        corpo = resposta.json()
        operador = corpo.get("operador_caixa", {})
        assert operador.get("usuario") == "operador_caixa"
        assert "BEGIN OPENSSH PRIVATE KEY" in operador.get("chave_privada", "")

        print("[OK] admin-api responde sem autenticação em /admin/credenciais.")
        print(f"[OK] usuário retornado: {operador['usuario']!r}")
        print("[OK] campo chave_privada presente no formato esperado (placeholder atual).")
    finally:
        processo.terminate()
        processo.wait(timeout=5)


if __name__ == "__main__":
    main()
