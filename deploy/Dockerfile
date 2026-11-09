# Sistema de Recarga do RU — imagem única da máquina.
#
# Contém: portal público (Etapa 1), painel de gerenciamento (Etapa 2/3) e
# admin-api (Etapa 3). Todos rodam no mesmo container; painel e admin-api
# escutam apenas em 127.0.0.1 (portas 8081 e 9090). Etapas seguintes (SSH
# para operador_caixa, daemon de conciliação de caixa) serão adicionadas
# conforme forem implementadas.

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libzbar0 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ru_web

WORKDIR /app

# --- Portal público (porta 8000, exposta) ---
COPY services/portal-publico/requirements.txt /app/requirements-portal.txt
RUN pip install --no-cache-dir -r /app/requirements-portal.txt

COPY services/portal-publico/ /app/

RUN mkdir -p /tmp/ru_uploads \
    && chmod 750 /app/legacy/validar_matricula.sh \
    && chown -R ru_web:ru_web /app /tmp/ru_uploads

# --- Admin-API (porta 9090, 127.0.0.1 apenas) ---
COPY services/admin-api/requirements.txt /opt/admin-api/requirements.txt
RUN pip install --no-cache-dir -r /opt/admin-api/requirements.txt
COPY services/admin-api/ /opt/admin-api/

# --- Painel de Gerenciamento (porta 8081, 127.0.0.1 apenas) ---
COPY services/painel-gerenciamento/requirements.txt /opt/painel/requirements.txt
RUN pip install --no-cache-dir -r /opt/painel/requirements.txt
COPY services/painel-gerenciamento/ /opt/painel/

# --- Entrypoint ---
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod 0700 /entrypoint.sh && chown root:root /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
