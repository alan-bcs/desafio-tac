#!/bin/bash
# Entrypoint da máquina. Roda como root só para provisionar a flag do usuário
# ru_web com o dono/permissão corretos, depois derruba privilégio e sobe o
# portal público. Etapas seguintes (serviços internos, SSH, daemon de
# conciliação) serão adicionadas aqui conforme forem implementadas.
set -euo pipefail

FLAG1="FLAG{RU_qr_c0de_nao_e_so_pra_leitura_7f3a1c}"

echo "${FLAG1}" > /home/ru_web/user.txt
chown ru_web:ru_web /home/ru_web/user.txt
chmod 440 /home/ru_web/user.txt

exec su -s /bin/bash ru_web -c "python3 /app/app.py"
