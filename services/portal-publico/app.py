"""Portal público de recarga de créditos do Restaurante Universitário (RU).

Permite ao aluno enviar a foto da carteirinha para leitura automática do QR Code
em vez de digitar a matrícula manualmente, integrando com o script legado de
validação de matrícula do sistema acadêmico antigo.
"""

import os
import uuid

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for
from PIL import Image, UnidentifiedImageError
from pyzbar.pyzbar import decode

UPLOAD_DIR = "/tmp/ru_uploads"
LEGACY_SCRIPT = "/app/legacy/validar_matricula.sh"
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-nao-usar-em-producao")


def decodificar_qrcode(caminho_imagem):
    """Lê o QR Code de uma imagem de carteirinha e retorna o conteúdo como texto."""
    try:
        imagem = Image.open(caminho_imagem)
    except UnidentifiedImageError:
        return None

    resultados = decode(imagem)
    if not resultados:
        return None

    return resultados[0].data.decode("utf-8", errors="replace").strip()


def validar_matricula_legado(conteudo_qrcode):
    """Repassa os dados lidos do QR Code para o script legado de validação."""
    if "|" in conteudo_qrcode:
        matricula = ""
        curso = ""
        for campo in conteudo_qrcode.split("|"):
            if ":" in campo:
                k, v = campo.split(":", 1)
                k = k.strip().upper()
                if "MATRICULA" in k:
                    matricula = v.strip()
                elif "CURSO" in k:
                    curso = v.strip()
        comando = f"bash {LEGACY_SCRIPT} {matricula} {curso}".strip()
    else:
        comando = f"bash {LEGACY_SCRIPT} {conteudo_qrcode}"

    return os.popen(comando).read()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/beta", methods=["GET"])
def beta():
    return render_template("beta.html")


@app.route("/carterinha-teste.jpg", methods=["GET"])
@app.route("/carteirinha-teste.jpg", methods=["GET"])
def carterinha_teste():
    return send_from_directory(STATIC_DIR, "carterinha-teste.jpg")


@app.route("/upload", methods=["POST"])
@app.route("/beta", methods=["POST"])
def upload():
    arquivo = request.files.get("carteirinha")
    if not arquivo or arquivo.filename == "":
        flash("Selecione a foto da carteirinha antes de enviar.")
        return redirect(url_for("beta"))

    nome_arquivo = f"{uuid.uuid4().hex}_{arquivo.filename}"
    caminho = os.path.join(UPLOAD_DIR, nome_arquivo)
    arquivo.save(caminho)

    matricula = decodificar_qrcode(caminho)
    if matricula is None:
        flash("Não foi possível ler o QR Code da carteirinha. Tente outra foto.")
        return redirect(url_for("beta"))

    saida_legado = validar_matricula_legado(matricula)

    return render_template("resultado.html", matricula=matricula, saida=saida_legado)


@app.route("/healthz", methods=["GET"])
def healthz():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
