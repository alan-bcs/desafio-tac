# Sistema de Recarga do RU — Boot2Root (03-ru)

Máquina Boot2Root em container Docker, desenvolvida para trabalho da disciplina de
Segurança Ofensiva. Narrativa: um portal fictício da UnB para recarga de créditos do
Restaurante Universitário (RU), onde o aluno faz upload da foto da carteirinha para
leitura automática do QR Code em vez de digitar a matrícula manualmente.

## Status

Implementação das quatro etapas presente; validação integrada final ainda pendente. Ver [`docs/decisoes.md`](docs/decisoes.md) para o estado
atual das decisões técnicas e [`docs/kill-chain.md`](docs/kill-chain.md) para a cadeia
de exploração completa.

## Visão geral da kill chain

| Etapa | Técnica | Resultado |
|---|---|---|
| 1 — Acesso inicial | Command Injection via conteúdo de QR Code decodificado | Shell como `ru_web`, flag 1 |
| 2 — Pivot interno | Enumeração e acesso aos serviços internos a partir do shell `ru_web` | Acesso ao painel interno |
| 3 — Exploração de serviço interno | IDOR na API administrativa interna (enumeração de operadores por ID) | Vazamento de credencial de `operador_caixa`, flag 2 |
| 4 — Escalação de privilégio | Race condition (symlink/TOCTOU) em job de conciliação de caixa rodando como root | Shell root, flag 3 |

Cada etapa usa uma técnica distinta das demais e distinta do que já foi usado nas
máquinas anteriores da disciplina (nenhuma reutiliza sudo-argument-injection).

## Estrutura do repositório

```text
desafio-tac-toctou/
├── deploy/                      # Dockerfile, entrypoint.sh, docker-compose.yml
├── services/
│   ├── portal-publico/          # App Flask pública — upload/leitura de QR Code (porta 8000, exposta)
│   ├── painel-gerenciamento/    # Serviço interno de consulta de operadores (porta 8081, 127.0.0.1)
│   └── admin-api/               # API interna sem autenticação, vulnerável a IDOR (porta 9090, 127.0.0.1)
├── privesc/                     # Daemon/script de "conciliação noturna de caixa" (root, intervalo 90s)
├── seed/
│   └── qrcodes/                 # QR Codes de exemplo/válidos para teste manual
└── docs/                        # Decisões técnicas, guia de execução, histórico
```

## Como rodar

```bash
cd deploy
docker compose up --build -d
```

- Portal público: `http://localhost:8000`
- SSH (para `operador_caixa` após a Etapa 3): `ssh -p 2222 operador_caixa@localhost`

Para derrubar: `docker compose down`.

### Chaves SSH do desafio

O Dockerfile gera automaticamente um **novo par ed25519 a cada build efetivo**.
Não é necessário criar, transferir ou commitar `chave_operador_caixa.pem`.
A API interna lê a chave privada gerada em
`/opt/admin-api/dados/chave_operador_caixa.pem`; a chave pública correspondente
é instalada em `/home/operador_caixa/.ssh/authorized_keys`.
A chave privada é legível somente por root dentro da imagem; `ru_web` não deve
conseguir lê-la diretamente. O campo `chave_privada` do endpoint do operador 3
é o caminho intencional para obtê-la.

**Rede e Portas:** o SSH está publicado na porta host `2222` e o Portal Web na porta `8000`, permitindo conexões diretas tanto em localhost quanto através da rede local pelos demais participantes da disciplina.

Para confirmar o provisionamento após subir a máquina:

```bash
sudo docker exec ru-machine python3 -c 'import json,urllib.request; d=json.load(urllib.request.urlopen("http://127.0.0.1:9090/api/v1/operadores/3")); print("Chave presente:", d["chave_privada"].startswith("-----BEGIN OPENSSH PRIVATE KEY-----"))'
sudo docker exec -u ru_web ru-machine sh -c 'test ! -r /opt/admin-api/dados/chave_operador_caixa.pem && echo "ru_web sem leitura direta: OK"'
```

Não inclua a chave privada em commits ou ZIPs públicos: ela é gerada no build.


## Documentação

- [`docs/kill-chain.md`](docs/kill-chain.md) — cadeia de exploração completa, passo a passo, com justificativa de design de cada etapa.
- [`docs/decisoes.md`](docs/decisoes.md) — tabela de decisões técnicas (credencial, portas, usuários, intervalo de cron, etc.) com status e justificativa.
- [`docs/guia-execucao.md`](docs/guia-execucao.md) — passo a passo manual reproduzível para jogar a máquina do zero (a preencher conforme a implementação avança).
- [`docs/checklist-qa.md`](docs/checklist-qa.md) — checklist de validação final antes da entrega.

## Regras de design (resumo)

- Dificuldade vem de raciocínio e encadeamento — nunca de força bruta, arquivos escondidos aleatoriamente ou adivinhação cega.
- Cada vulnerabilidade tem um único caminho intencional de exploração.
- `root` dentro do container nunca significa acesso real ao host (sem `--privileged`, sem `docker.sock` montado, sem mounts sensíveis do host).
- Comentários em código shipado nunca descrevem a vulnerabilidade ou a técnica de exploração.
