# Checklist de QA Final — Sistema de Recarga do RU

**Atualizado em:** 10/11/2026  
**Legenda:** `[x]` comprovado nos testes relatados; `[ ]` pendente de validação. A implementação não equivale, por si só, a um teste de ponta a ponta.

## Build e infraestrutura

- [x] `docker compose -f deploy/docker-compose.yml up --build -d` criou um container `ru-machine` em estado `Up`, após corrigir uma linha vazia antes do shebang de `deploy/entrypoint.sh`.
- [x] `docker ps` mostrou as publicações `0.0.0.0:8000->8000/tcp` e `127.0.0.1:2222->22/tcp`.
- [ ] Validar que o container permanece estável após períodos prolongados e reinícios.
- [ ] Validar `docker compose -f deploy/docker-compose.yml down` e nova subida limpa.
- [x] O Compose apresentado não usa `--privileged`, `docker.sock` ou mounts sensíveis.
- [x] O Dockerfile define `/entrypoint.sh` como `0700 root:root`.
- [ ] Confirmar a imagem final reconstruída após eventuais alterações de documentação/código.

## Isolamento de rede

- [x] As portas 8081 e 9090 não são publicadas no host pelo Compose atual.
- [x] `curl http://127.0.0.1:9090/...` no Kali falhou, enquanto consulta à API executada dentro do container funcionou.
- [ ] Confirmar com inspeção de sockets que painel e API escutam apenas em `127.0.0.1` **dentro** do container.
- [ ] Testar ausência de acesso não pretendido pela rede Docker e por outras interfaces.
- [ ] Para distribuição a jogadores remotos, definir conscientemente como publicar o SSH (atualmente restrito ao loopback do host).

## Etapa 1 — Command Injection via QR Code

- [x] Testes de decodificação e lógica Flask registrados na documentação anterior (`tests/test_decode_qr.py`, `tests/test_app_client.py`).
- [ ] Reexecutar os testes no estado final do repositório.
- [ ] Testar upload malicioso no portal real (`:8000`) e obter shell como `ru_web`.
- [ ] Confirmar leitura de `/home/ru_web/user.txt` por essa shell.

## Etapa 2 — Descoberta dos serviços internos

- [x] API respondeu em `127.0.0.1:9090` a partir de processo dentro do container.
- [ ] Testar descoberta das portas 8081/9090 e navegação do painel **como `ru_web`**, sem `docker exec` administrativo.
- [ ] Verificar que o painel oferece pistas suficientes para localizar a rota de operadores, sem exigir adivinhação.
- [ ] Confirmar que o jogador consegue extrair e transferir a chave a partir do acesso inicial.

## Etapa 3 — IDOR e SSH

- [x] `GET /api/v1/operadores/3` retornou `usuario: operador_caixa` e `chave_privada` no formato `-----BEGIN OPENSSH PRIVATE KEY-----`.
- [x] A chave local configurada para o operador autenticou via SSH na porta `2222`.
- [x] A sessão SSH mostrou `uid=1001(operador_caixa)` e `gid=1001(operador_caixa)`.
- [x] A flag 2 foi lida em `/home/operador_caixa/user.txt`.
- [ ] Comparar byte a byte a chave retornada pela API com o arquivo `.pem` local, para provar identidade exata (além da configuração esperada).
- [ ] Verificar que `ru_web` não consegue ler diretamente `/opt/admin-api/dados/chave_operador_caixa.pem` nem acessar outras credenciais que permitam pular a IDOR.
- [ ] Testar a cadeia completa IDOR → salvar chave **obtida da resposta** → SSH, sem reutilizar o arquivo de desenvolvimento.

## Etapa 4 — Symlink TOCTOU

- [x] `ps aux` na sessão SSH mostrou `python3 -u /opt/conciliacao.py` executado como root.
- [x] `/opt/conciliacao.py` é legível por `operador_caixa`; `/opt/helper_conciliacao.sh` não é legível por esse usuário.
- [x] `/var/ru/caixa` é gravável pelo grupo `operador_caixa`; `dados.csv` pode ser modificado e `conciliacao.tmp` substituído.
- [x] A exploração via SSH sobrescreveu o helper por symlink e produziu `/var/ru/prova_ssh.txt` contendo `uid=0(root) gid=0(root) groups=0(root)`.
- [x] Acesso direto a `/root/root.txt` foi negado a `operador_caixa`.
- [ ] Demonstrar obtenção da flag root pela cadeia de exploração, sem privilégios administrativos do host.
- [ ] Repetir o exploit após recriação limpa para avaliar consistência e timing.
- [ ] Confirmar restauração do helper original após o teste destrutivo.

## Código e documentação

- [ ] **Remover comentários que entregam a técnica** em `privesc/conciliacao.py`, como `# Janela TOCTOU intencional` e `# Reabre o caminho, permitindo a troca por symlink`.
- [ ] Confirmar que `privesc/demo_toctou.py` não é incluído na distribuição, caso permaneça no repositório (o Dockerfile mostrado não o copia).
- [ ] Conferir flags entre `deploy/entrypoint.sh`, testes automatizados e metadados da plataforma.
- [x] Documentação atualizada para registrar SSH e exploração TOCTOU efetivamente observados.
- [ ] Playtest integral, do portal até a flag root, sem `docker exec`.

## Variedade de técnicas

- [x] Técnicas distintas: command injection, falha de controle de acesso por referência direta a objeto (IDOR) e symlink TOCTOU.
- [x] A etapa 4 não depende de sudo-argument-injection.


## Provisionamento autossuficiente (versão atual)

- [x] Dockerfile não depende de `.pem` ou `.pub` existentes no host.
- [x] Build gera chave privada ed25519 e instala a pública correspondente para SSH.
- [x] API e painel configurados para `127.0.0.1` dentro do container.
- [ ] Validar em build Docker limpo que o endpoint do operador 3 retorna a chave.
- [ ] Validar que `ru_web` não lê diretamente o arquivo `.pem`.
- [ ] Validar login SSH com a chave retornada pela API após o novo build.
- [ ] Testar a kill chain completa desde o QR Code até a flag root.
