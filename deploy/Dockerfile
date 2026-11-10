
# Sistema de Recarga do RU — imagem unica da maquina.
#
# Etapa 1: Portal publico
# Etapas 2/3: Painel, Admin-API e SSH
# Etapa 4: Job de conciliacao vulneravel

FROM python:3.11-slim

# --- Dependencias do sistema ---
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libzbar0 \
        openssh-server \
    && rm -rf /var/lib/apt/lists/*

# --- Usuarios ---
RUN useradd -m -s /bin/bash ru_web \
    && useradd -m -s /bin/bash operador_caixa

# --- SSH do operador de caixa ---
RUN mkdir -p /run/sshd /home/operador_caixa/.ssh \
    && chmod 700 /home/operador_caixa/.ssh \
    && chown operador_caixa:operador_caixa /home/operador_caixa/.ssh \
    && printf '\nPasswordAuthentication no\nKbdInteractiveAuthentication no\nPermitRootLogin no\nPubkeyAuthentication yes\nAllowUsers operador_caixa\n' >> /etc/ssh/sshd_config \
    && ssh-keygen -A

# --- Diretorio de conciliacao ---
RUN mkdir -p /var/ru/caixa \
    && chown root:operador_caixa /var/ru/caixa \
    && chmod 2770 /var/ru/caixa \
    && touch /var/ru/caixa/conciliacao.tmp \
    && chown operador_caixa:operador_caixa /var/ru/caixa/conciliacao.tmp

# --- Dados controlados pelo operador ---
RUN printf 'data,valor\n2026-11-09,25.00\n' > /var/ru/caixa/dados.csv \
    && chown operador_caixa:operador_caixa /var/ru/caixa/dados.csv \
    && chmod 660 /var/ru/caixa/dados.csv

# --- Job de conciliacao (Etapa 4) ---
COPY privesc/conciliacao.py /opt/conciliacao.py

RUN chown root:root /opt/conciliacao.py \
    && chmod 755 /opt/conciliacao.py

COPY privesc/helper_conciliacao.sh /opt/helper_conciliacao.sh

RUN chown root:root /opt/helper_conciliacao.sh \
    && chmod 700 /opt/helper_conciliacao.sh

WORKDIR /app

# --- Portal publico (porta 8000) ---
COPY services/portal-publico/requirements.txt /app/requirements-portal.txt

RUN pip install --no-cache-dir -r /app/requirements-portal.txt

COPY services/portal-publico/ /app/

RUN mkdir -p /tmp/ru_uploads \
    && chmod 750 /app/legacy/validar_matricula.sh \
    && chown -R ru_web:ru_web /app /tmp/ru_uploads

# --- Admin-API (porta 9090) ---
COPY services/admin-api/requirements.txt /opt/admin-api/requirements.txt

RUN pip install --no-cache-dir -r /opt/admin-api/requirements.txt

COPY services/admin-api/ /opt/admin-api/

# Par de chaves EXCLUSIVO desta imagem do CTF: nunca depende do host ou Git.
# A API (root) le a privada; operador_caixa usa apenas a publica.
RUN rm -f /opt/admin-api/dados/chave_operador_caixa.pem \
          /opt/admin-api/dados/chave_operador_caixa.pem.pub \
    && ssh-keygen -q -t ed25519 \
         -f /opt/admin-api/dados/chave_operador_caixa.pem \
         -N "" -C "operador_caixa@ru-ctf" \
    && install -o operador_caixa -g operador_caixa -m 600 \
         /opt/admin-api/dados/chave_operador_caixa.pem.pub \
         /home/operador_caixa/.ssh/authorized_keys \
    && chmod 600 /opt/admin-api/dados/chave_operador_caixa.pem \
    && chown root:root /opt/admin-api/dados/chave_operador_caixa.pem \
    && rm -f /opt/admin-api/dados/chave_operador_caixa.pem.pub \
    && chmod 755 /opt/admin-api /opt/admin-api/dados


# --- Painel de Gerenciamento (porta 8081) ---
COPY services/painel-gerenciamento/requirements.txt /opt/painel/requirements.txt

RUN pip install --no-cache-dir -r /opt/painel/requirements.txt

COPY services/painel-gerenciamento/ /opt/painel/

# --- Entrypoint ---
COPY deploy/entrypoint.sh /entrypoint.sh

RUN chmod 0700 /entrypoint.sh \
    && chown root:root /entrypoint.sh

EXPOSE 8000 22

ENTRYPOINT ["/entrypoint.sh"]

