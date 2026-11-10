#!/bin/bash

# Entrypoint do Sistema de Recarga do RU.
# Executado inicialmente como root.

set -euo pipefail

# --- Flag da Etapa 1 ---
FLAG1="FLAG{RU_qr_c0de_nao_e_so_pra_leitura_7f3a1c}"

printf '%s\n' "$FLAG1" > /home/ru_web/user.txt
chown ru_web:ru_web /home/ru_web/user.txt
chmod 440 /home/ru_web/user.txt

# --- Flag da Etapa 3 ---
FLAG2="FLAG{RU_1d0r_ssh_operador_6b2f9a}"

printf '%s\n' "$FLAG2" > /home/operador_caixa/user.txt
chown operador_caixa:operador_caixa /home/operador_caixa/user.txt
chmod 400 /home/operador_caixa/user.txt

# --- Flag root (Etapa 4) ---
FLAG_ROOT="FLAG{RU_t0ct0u_syml1nk_r00t_9c4e2b}"

mkdir -p /root
printf '%s\n' "$FLAG_ROOT" > /root/root.txt
chown root:root /root/root.txt
chmod 600 /root/root.txt

# --- Servidor SSH ---
mkdir -p /run/sshd
/usr/sbin/sshd

# --- Servicos internos ---
python3 /opt/admin-api/app.py &

python3 /opt/painel/app.py &

# --- Job privilegiado de conciliacao ---
python3 -u /opt/conciliacao.py &

# --- Portal publico ---
exec su -s /bin/bash ru_web -c "python3 /app/app.py"

