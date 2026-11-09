#!/bin/bash
# Entrypoint da máquina. Roda como root para provisionar flags e subir os
# serviços internos (admin-api e painel) em background, depois derruba
# privilégio e sobe o portal público em foreground.
# Etapas seguintes (SSH, daemon de conciliação) serão adicionadas aqui
# conforme forem implementadas.
set -euo pipefail

# ── Flags ─────────────────────────────────────────────────────────────────
FLAG1="FLAG{RU_qr_c0de_nao_e_so_pra_leitura_7f3a1c}"

echo "${FLAG1}" > /home/ru_web/user.txt
chown ru_web:ru_web /home/ru_web/user.txt
chmod 440 /home/ru_web/user.txt

# ── Serviços internos (bind 127.0.0.1, inacessíveis de fora) ─────────────
# Admin-API — porta 9090
python3 /opt/admin-api/app.py &

# Painel de Gerenciamento — porta 8081
python3 /opt/painel/app.py &

# ── Portal público (foreground, porta 8000) ───────────────────────────────
exec su -s /bin/bash ru_web -c "python3 /app/app.py"
