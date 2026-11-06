# Sistema de Recarga do RU — imagem única da máquina.
#
# Por enquanto só o portal público (Etapa 1) está implementado. As etapas
# seguintes (painel de gerenciamento, admin-api, SSH para operador_caixa,
# daemon de conciliação de caixa) rodam no mesmo container, cada uma em
# 127.0.0.1 numa porta distinta, e serão adicionadas aqui conforme forem
# implementadas.

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libzbar0 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ru_web

WORKDIR /app

COPY services/portal-publico/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/portal-publico/ /app/

RUN mkdir -p /tmp/ru_uploads \
    && chmod 750 /app/legacy/validar_matricula.sh \
    && chown -R ru_web:ru_web /app /tmp/ru_uploads

COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod 0700 /entrypoint.sh && chown root:root /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
