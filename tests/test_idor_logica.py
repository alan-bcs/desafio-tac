"""Teste de camada 1 (lógica isolada, fora do Flask do painel): sobe a
admin-api como processo real e confirma, com `requests.get()` puro, que os
endpoints de IDOR expõem credenciais sem controle de autorização.

Valida:
  1. GET /api/v1/operadores retorna a lista de operadores (sem credenciais).
  2. GET /api/v1/operadores/1 retorna operador sem chave SSH.
  3. GET /api/v1/operadores/3 retorna operador_caixa COM chave SSH privada.
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
        # --- 1. Listagem de operadores --------------------------------
        resp_lista = requests.get(
            f"http://127.0.0.1:{ADMIN_API_PORT}/api/v1/operadores", timeout=5
        )
        assert resp_lista.status_code == 200, f"status inesperado na listagem: {resp_lista.status_code}"
        lista = resp_lista.json()
        assert isinstance(lista, list) and len(lista) >= 3, f"lista inesperada: {lista}"
        print(f"[OK] /api/v1/operadores retorna {len(lista)} operadores.")

        # --- 2. Operador sem chave (ID 1) ------------------------------
        resp_op1 = requests.get(
            f"http://127.0.0.1:{ADMIN_API_PORT}/api/v1/operadores/1", timeout=5
        )
        assert resp_op1.status_code == 200, f"status inesperado para ID 1: {resp_op1.status_code}"
        dados_op1 = resp_op1.json()
        assert dados_op1.get("chave_privada") is None, "operador 1 não deveria ter chave_privada"
        print(f"[OK] /api/v1/operadores/1 retorna operador sem chave SSH (campo nulo).")

        # --- 3. operador_caixa (ID 3) com chave privada ---------------
        resp_op3 = requests.get(
            f"http://127.0.0.1:{ADMIN_API_PORT}/api/v1/operadores/3", timeout=5
        )
        assert resp_op3.status_code == 200, f"status inesperado para ID 3: {resp_op3.status_code}"
        dados_op3 = resp_op3.json()
        assert dados_op3.get("usuario") == "operador_caixa", f"usuario inesperado: {dados_op3.get('usuario')}"
        assert dados_op3.get("chave_privada") is not None, "chave_privada ausente para operador_caixa"
        assert "BEGIN OPENSSH PRIVATE KEY" in dados_op3["chave_privada"], "chave_privada não contém header esperado"
        print(f"[OK] /api/v1/operadores/3 retorna operador_caixa com chave SSH privada.")

        print("[OK] IDOR validado: credenciais expostas sem controle de autorização.")

    finally:
        processo.terminate()
        processo.wait(timeout=5)


if __name__ == "__main__":
    main()
