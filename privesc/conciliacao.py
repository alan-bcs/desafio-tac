
#!/usr/bin/env python3

import stat
import subprocess
import time
from pathlib import Path

DIRETORIO = Path("/var/ru/caixa")
ENTRADA = DIRETORIO / "dados.csv"
RELATORIO = DIRETORIO / "conciliacao.tmp"


def conciliar():
    print("[JOB] Iniciando conciliacao...", flush=True)

    # Verifica a entrada do operador
    if not ENTRADA.is_file():
        print("[JOB] Dados de entrada ausentes.", flush=True)
        return

    # Le os dados fornecidos pelo operador
    dados = ENTRADA.read_text()

    # Verifica a saida sem seguir symlinks
    try:
        info = RELATORIO.lstat()
    except FileNotFoundError:
        print("[JOB] Relatorio nao encontrado.", flush=True)
        return

    if not stat.S_ISREG(info.st_mode):
        print("[JOB] Arquivo invalido: nao e regular.", flush=True)
        return

    print("[JOB] Arquivo regular validado.", flush=True)

    
    time.sleep(15)

    with open(RELATORIO, "w") as arquivo:
        arquivo.write(dados)

    print("[JOB] Relatorio atualizado.", flush=True)
    subprocess.run(
        ["/bin/bash", "/opt/helper_conciliacao.sh"],
        check=True
    )


if __name__ == "__main__":
    while True:
        try:
            conciliar()
        except Exception as erro:
            print(f"[JOB] Erro: {erro}", flush=True)

        time.sleep(90)

